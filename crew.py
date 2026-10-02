# crew.py

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import streamlit as st
from groq import Groq

from crewai import Agent, Crew, Process, Task, BaseLLM

from research_manager import create_research_manager
from web_researcher import create_web_researcher
from academic_researcher import create_academic_researcher
from industry_researcher import create_industry_researcher
from synthesizer import create_synthesizer


# ============================================================
# CONFIGURATION
# ============================================================

MODEL_NAME = "openai/gpt-oss-120b"


# ============================================================
# SECRET HELPER
# ============================================================

def get_secret(name: str) -> str:
    """
    Read a secret from environment variables first,
    then Streamlit secrets.
    """

    value = os.getenv(name)

    if value:
        return value

    try:
        value = st.secrets[name]

        if value:
            return str(value)

    except Exception:
        pass

    return ""


# ============================================================
# CUSTOM GROQ LLM
# ============================================================

class GroqCrewLLM(BaseLLM):
    """
    Custom CrewAI LLM using the official Groq Python SDK.

    This is used instead of CrewAI's OpenAI-compatible
    provider because Groq requires the exact model ID:

        openai/gpt-oss-120b
    """

    def __init__(
        self,
        model: str = MODEL_NAME,
        temperature: float = 0.2,
    ):
        super().__init__(
            model=model,
            temperature=temperature,
        )

        api_key = get_secret("GROQ_API_KEY")

        if not api_key:
            raise ValueError(
                "GROQ_API_KEY is not configured. "
                "Add GROQ_API_KEY to Streamlit Cloud Secrets."
            )

        self.client = Groq(
            api_key=api_key
        )

    # --------------------------------------------------------
    # CLEAN VALUES
    # --------------------------------------------------------

    def _clean_value(self, value):

        if isinstance(value, dict):

            cleaned = {}

            for key, item in value.items():

                # CrewAI can add this field.
                # Groq Chat Completions does not accept it.
                if key == "cache_breakpoint":
                    continue

                cleaned[key] = self._clean_value(item)

            return cleaned

        if isinstance(value, list):

            return [
                self._clean_value(item)
                for item in value
            ]

        if isinstance(value, tuple):

            return [
                self._clean_value(item)
                for item in value
            ]

        return value

    # --------------------------------------------------------
    # CLEAN MESSAGES
    # --------------------------------------------------------

    def _clean_messages(self, messages):

        if isinstance(messages, str):

            return [
                {
                    "role": "user",
                    "content": messages,
                }
            ]

        clean_messages = []

        for message in messages:

            if isinstance(message, dict):

                cleaned_message = self._clean_value(
                    message
                )

                clean_messages.append(
                    cleaned_message
                )

                continue

            try:

                cleaned_message = {
                    "role": getattr(
                        message,
                        "role",
                        "user",
                    ),
                    "content": self._clean_value(
                        getattr(
                            message,
                            "content",
                            "",
                        )
                    ),
                }

                tool_calls = getattr(
                    message,
                    "tool_calls",
                    None,
                )

                if tool_calls:

                    cleaned_message[
                        "tool_calls"
                    ] = self._clean_value(
                        tool_calls
                    )

                name = getattr(
                    message,
                    "name",
                    None,
                )

                if name:

                    cleaned_message[
                        "name"
                    ] = name

                tool_call_id = getattr(
                    message,
                    "tool_call_id",
                    None,
                )

                if tool_call_id:

                    cleaned_message[
                        "tool_call_id"
                    ] = tool_call_id

                clean_messages.append(
                    cleaned_message
                )

            except Exception:

                clean_messages.append(
                    {
                        "role": "user",
                        "content": str(message),
                    }
                )

        return clean_messages

    # --------------------------------------------------------
    # LLM CALL
    # --------------------------------------------------------

    def call(
        self,
        messages,
        tools=None,
        callbacks=None,
        available_functions=None,
        **kwargs,
    ) -> Any:

        clean_messages = self._clean_messages(
            messages
        )

        request_kwargs = {
            "model": self.model,
            "messages": clean_messages,
            "temperature": self.temperature,
        }

        # Tool/function calling
        if tools:

            request_kwargs["tools"] = (
                self._clean_value(tools)
            )

            request_kwargs["tool_choice"] = "auto"

        response = (
            self.client
            .chat
            .completions
            .create(
                **request_kwargs
            )
        )

        message = (
            response
            .choices[0]
            .message
        )

        # Return native tool calls to CrewAI.
        tool_calls = getattr(
            message,
            "tool_calls",
            None,
        )

        if tool_calls:

            return tool_calls

        return message.content or ""

    # --------------------------------------------------------
    # CREWAI CAPABILITIES
    # --------------------------------------------------------

    def supports_function_calling(self) -> bool:
        return True

    def supports_stop_words(self) -> bool:
        return False

    def get_context_window_size(self) -> int:
        return 131072


# ============================================================
# CREATE LLM
# ============================================================

def create_llm():

    return GroqCrewLLM(
        model=MODEL_NAME,
        temperature=0.2,
    )


# ============================================================
# OUTPUT HELPER
# ============================================================

def get_output_text(result) -> str:

    if result is None:
        return ""

    raw = getattr(
        result,
        "raw",
        None,
    )

    if raw is not None:
        return str(raw)

    output = getattr(
        result,
        "output",
        None,
    )

    if output is not None:
        return str(output)

    return str(result)


# ============================================================
# STATUS HELPER
# ============================================================

def update_status(
    status_callback,
    key: str,
    message: str,
):

    if status_callback is None:
        return

    try:

        status_callback(
            key,
            message,
        )

    except Exception:
        # Never let UI updates break the research pipeline.
        pass


# ============================================================
# WEB RESEARCH WORKER
# ============================================================

def run_web_research(
    research_question: str,
    research_plan: str,
    status_callback=None,
):

    try:

        update_status(
            status_callback,
            "web",
            "Web researcher is working...",
        )

        llm = create_llm()

        web_researcher = create_web_researcher(
            llm=llm
        )

        web_task = Task(
            description=f"""
Conduct web research for the following research project.

RESEARCH QUESTION:

{research_question}

RESEARCH PLAN:

{research_plan}

You are the Web Research Specialist.

Use your available web search and webpage-reading tools.

Focus on:

- recent information
- authoritative websites
- official sources
- reputable organizations
- current statistics
- documented facts
- relevant reports
- recent developments

For every important finding, provide the source URL
whenever possible.

Do not simply produce a list of links.

Explain:

- what the source says
- why it matters
- how it relates to the research question

Clearly distinguish facts from opinions or claims.

Do not invent sources or statistics.

Return structured research findings that another agent
can use to write the final report.
""",
            expected_output="""
Detailed web research findings including:

- key findings
- supporting evidence
- source names
- source URLs
- relevant statistics
- important recent developments
- limitations or conflicting evidence
""",
            agent=web_researcher,
        )

        web_crew = Crew(
            agents=[
                web_researcher
            ],
            tasks=[
                web_task
            ],
            process=Process.sequential,
            verbose=False,
        )

        result = web_crew.kickoff()

        findings = get_output_text(
            result
        )

        update_status(
            status_callback,
            "web",
            "Web research completed.",
        )

        return findings

    except Exception as exc:

        update_status(
            status_callback,
            "web",
            f"Web research failed: {exc}",
        )

        raise


# ============================================================
# ACADEMIC RESEARCH WORKER
# ============================================================

def run_academic_research(
    research_question: str,
    research_plan: str,
    status_callback=None,
):

    try:

        update_status(
            status_callback,
            "academic",
            "Academic researcher is working...",
        )

        llm = create_llm()

        academic_researcher = create_academic_researcher(
            llm=llm
        )

        academic_task = Task(
            description=f"""
Conduct academic research for the following project.

RESEARCH QUESTION:

{research_question}

RESEARCH PLAN:

{research_plan}

You are the Academic Research Specialist.

Use your academic search tools to find relevant
peer-reviewed research, scholarly papers, studies,
and academic literature.

Focus on:

- established research
- recent studies
- systematic reviews where available
- important theoretical frameworks
- empirical evidence
- research findings
- methodological limitations

For important papers, provide:

- paper title
- authors when available
- publication year
- journal or venue when available
- DOI or source URL when available
- key finding
- relevance to this research

Do not invent papers, authors, statistics, or citations.

Clearly identify where evidence is limited or mixed.

Return structured academic findings that another agent
can use in the final report.
""",
            expected_output="""
Detailed academic research findings including:

- important studies
- paper titles
- authors
- publication years
- key findings
- academic evidence
- DOI/source URLs when available
- limitations
- areas of disagreement
""",
            agent=academic_researcher,
        )

        academic_crew = Crew(
            agents=[
                academic_researcher
            ],
            tasks=[
                academic_task
            ],
            process=Process.sequential,
            verbose=False,
        )

        result = academic_crew.kickoff()

        findings = get_output_text(
            result
        )

        update_status(
            status_callback,
            "academic",
            "Academic research completed.",
        )

        return findings

    except Exception as exc:

        update_status(
            status_callback,
            "academic",
            f"Academic research failed: {exc}",
        )

        raise


# ============================================================
# INDUSTRY RESEARCH WORKER
# ============================================================

def run_industry_research(
    research_question: str,
    research_plan: str,
    status_callback=None,
):

    try:

        update_status(
            status_callback,
            "industry",
            "Industry researcher is working...",
        )

        llm = create_llm()

        industry_researcher = create_industry_researcher(
            llm=llm
        )

        industry_task = Task(
            description=f"""
Conduct industry and market research for the following
research project.

RESEARCH QUESTION:

{research_question}

RESEARCH PLAN:

{research_plan}

You are the Industry / Market Research Specialist.

Investigate the practical and commercial side of the topic.

Focus on:

- industry trends
- market developments
- companies and organizations
- products and services
- adoption
- business models
- pricing where relevant
- competitive landscape
- market statistics
- real-world implementations
- current challenges
- opportunities and risks

Use web research and webpage-reading tools.

Prefer primary sources, company reports, official
documentation, reputable industry reports, and credible
business sources.

For important findings, provide source URLs.

Do not invent market sizes, company claims, statistics,
or business information.

Clearly distinguish company claims from independently
verified evidence.

Return structured industry findings that another agent
can use in the final report.
""",
            expected_output="""
Detailed industry and market research including:

- market trends
- companies and organizations
- products/services
- adoption
- competitive information
- business models
- statistics
- practical applications
- risks
- source URLs
""",
            agent=industry_researcher,
        )

        industry_crew = Crew(
            agents=[
                industry_researcher
            ],
            tasks=[
                industry_task
            ],
            process=Process.sequential,
            verbose=False,
        )

        result = industry_crew.kickoff()

        findings = get_output_text(
            result
        )

        update_status(
            status_callback,
            "industry",
            "Industry research completed.",
        )

        return findings

    except Exception as exc:

        update_status(
            status_callback,
            "industry",
            f"Industry research failed: {exc}",
        )

        raise


# ============================================================
# SYNTHESIS
# ============================================================

def run_synthesis(
    research_question: str,
    research_plan: str,
    web_findings: str,
    academic_findings: str,
    industry_findings: str,
    status_callback=None,
):

    try:

        update_status(
            status_callback,
            "synthesizer",
            "Synthesizer is creating the final report...",
        )

        llm = create_llm()

        synthesizer = create_synthesizer(
            llm=llm
        )

        synthesis_task = Task(
            description=f"""
You are the lead research synthesizer.

Write a high-quality final research report based ONLY
on the research material provided below.

========================================================
RESEARCH QUESTION
========================================================

{research_question}

========================================================
RESEARCH PLAN
========================================================

{research_plan}

========================================================
WEB RESEARCH
========================================================

{web_findings}

========================================================
ACADEMIC RESEARCH
========================================================

{academic_findings}

========================================================
INDUSTRY / MARKET RESEARCH
========================================================

{industry_findings}

========================================================
REPORT STRUCTURE
========================================================

Create a professional research report using:

# Executive Summary

Give a concise overview of the most important findings.

# Introduction

Explain the research question and why the topic matters.

# Key Findings

Present the major findings from all research streams.

# Web Evidence

Summarize important web-based evidence and current
developments.

# Academic Evidence

Summarize relevant academic research and what it shows.

# Industry / Market Landscape

Discuss practical, commercial, and market developments.

# Cross-Source Analysis

Compare the web, academic, and industry evidence.

Identify:

- agreements
- disagreements
- evidence gaps
- important trends
- limitations

# Practical Implications

Explain what the evidence means in practical terms.

# Risks and Limitations

Identify uncertainty, limitations, missing evidence,
and potential biases.

# Conclusion

Provide a concise evidence-based conclusion.

# Sources

List the most important sources with URLs when available.

========================================================
IMPORTANT RULES
========================================================

1. Do not invent facts.

2. Do not invent citations.

3. Do not invent URLs.

4. If sources disagree, explain the disagreement.

5. Clearly distinguish evidence from interpretation.

6. Prefer evidence over unsupported claims.

7. Use information from all three research streams.

8. Do not mention internal agent names in the final report.

9. Do not fabricate academic papers.

10. Do not fabricate statistics.

11. Make the report readable and professional.

Return ONLY the final research report.
""",
            expected_output="""
A complete professional research report containing:

- Executive Summary
- Introduction
- Key Findings
- Web Evidence
- Academic Evidence
- Industry / Market Landscape
- Cross-Source Analysis
- Practical Implications
- Risks and Limitations
- Conclusion
- Sources
""",
            agent=synthesizer,
        )

        synthesis_crew = Crew(
            agents=[
                synthesizer
            ],
            tasks=[
                synthesis_task
            ],
            process=Process.sequential,
            verbose=False,
        )

        result = synthesis_crew.kickoff()

        final_report = get_output_text(
            result
        )

        update_status(
            status_callback,
            "synthesizer",
            "Final report completed.",
        )

        return final_report

    except Exception as exc:

        update_status(
            status_callback,
            "synthesizer",
            f"Synthesis failed: {exc}",
        )

        raise


# ============================================================
# MAIN RESEARCH PIPELINE
# ============================================================

def run_research(
    research_question: str,
    status_callback=None,
):
    """
    Complete research pipeline.

    1. Research Manager
    2. Web Research       ┐
    3. Academic Research  ├── run concurrently
    4. Industry Research  ┘
    5. Synthesizer
    """

    # ========================================================
    # VALIDATE QUESTION
    # ========================================================

    if not research_question:

        raise ValueError(
            "Please provide a research question."
        )

    research_question = (
        research_question.strip()
    )

    if not research_question:

        raise ValueError(
            "Please provide a research question."
        )

    # ========================================================
    # MANAGER
    # ========================================================

    update_status(
        status_callback,
        "manager",
        "Research Manager is creating the research plan...",
    )

    llm = create_llm()

    manager = create_research_manager(
        llm=llm
    )

    manager_task = Task(
        description=f"""
You are managing a multi-agent research project.

RESEARCH QUESTION:

{research_question}

Create a clear research plan for the specialist
researchers.

The plan must contain:

1. Main research objective.
2. Key questions that must be answered.
3. Important concepts and terminology.
4. Evidence that should be collected.
5. What should be investigated by:
   - Web Researcher
   - Academic Researcher
   - Industry / Market Researcher
6. Important risks, assumptions, and limitations.

Do NOT write the final report.

Create a concise but detailed research plan that the
specialist researchers can directly follow.
""",
        expected_output="""
A structured research plan containing:

- research objective
- key questions
- evidence requirements
- web research instructions
- academic research instructions
- industry research instructions
- limitations and considerations
""",
        agent=manager,
    )

    manager_crew = Crew(
        agents=[
            manager
        ],
        tasks=[
            manager_task
        ],
        process=Process.sequential,
        verbose=False,
    )

    manager_result = manager_crew.kickoff()

    research_plan = get_output_text(
        manager_result
    )

    update_status(
        status_callback,
        "manager",
        "Research strategy completed.",
    )

    # ========================================================
    # RUN SPECIALISTS IN PARALLEL
    # ========================================================

    specialist_results = {}

    with ThreadPoolExecutor(
        max_workers=3
    ) as executor:

        futures = {

            executor.submit(
                run_web_research,
                research_question,
                research_plan,
                status_callback,
            ): "web",

            executor.submit(
                run_academic_research,
                research_question,
                research_plan,
                status_callback,
            ): "academic",

            executor.submit(
                run_industry_research,
                research_question,
                research_plan,
                status_callback,
            ): "industry",
        }

        for future in as_completed(
            futures
        ):

            research_type = futures[
                future
            ]

            # This will raise the original exception
            # if a specialist failed.
            specialist_results[
                research_type
            ] = future.result()

    # ========================================================
    # GET RESULTS
    # ========================================================

    web_findings = specialist_results.get(
        "web",
        "",
    )

    academic_findings = specialist_results.get(
        "academic",
        "",
    )

    industry_findings = specialist_results.get(
        "industry",
        "",
    )

    # ========================================================
    # SYNTHESIZER
    # ========================================================

    final_report = run_synthesis(
        research_question=research_question,
        research_plan=research_plan,
        web_findings=web_findings,
        academic_findings=academic_findings,
        industry_findings=industry_findings,
        status_callback=status_callback,
    )

    # ========================================================
    # RETURN RESULT
    # ========================================================

    return {
        "report": final_report,

        "research_plan": research_plan,

        "web_research": web_findings,

        "academic_research": academic_findings,

        "industry_research": industry_findings,
    }
