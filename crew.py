# crew.py

import os
from typing import Any, Optional

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
    then fall back to Streamlit secrets.
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
# CUSTOM GROQ LLM FOR CREWAI
# ============================================================

class GroqCrewLLM(BaseLLM):
    """
    Custom CrewAI LLM implementation using the official
    Groq Python SDK directly.

    This avoids CrewAI's OpenAI-compatible provider changing:

        openai/gpt-oss-120b

    into:

        gpt-oss-120b

    which Groq does not accept.
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
    # CLEAN CREWAI MESSAGE
    # --------------------------------------------------------

    def _clean_value(self, value):
        """
        Recursively clean objects before sending them to Groq.

        In particular, CrewAI may add:

            cache_breakpoint

        to messages.

        Groq Chat Completions does not accept that field, so
        remove it before making the API request.
        """

        if isinstance(value, dict):

            cleaned = {}

            for key, item in value.items():

                # CrewAI/OpenAI-compatible metadata that Groq
                # Chat Completions does not accept.
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
    # CONVERT MESSAGE OBJECTS
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

            # Already a dictionary
            if isinstance(message, dict):

                cleaned_message = self._clean_value(
                    message
                )

                clean_messages.append(
                    cleaned_message
                )

                continue

            # CrewAI/OpenAI-style message object
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

                # Preserve tool calls when present.
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

                # Preserve tool-call related fields.
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
    # CREWAI LLM CALL
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

        # ----------------------------------------------------
        # GROQ REQUEST
        # ----------------------------------------------------

        request_kwargs = {
            "model": self.model,
            "messages": clean_messages,
            "temperature": self.temperature,
        }

        # ----------------------------------------------------
        # TOOL CALLING
        # ----------------------------------------------------

        if tools:

            request_kwargs["tools"] = (
                self._clean_value(tools)
            )

            request_kwargs["tool_choice"] = "auto"

        # ----------------------------------------------------
        # CALL GROQ
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # TOOL CALL RESPONSE
        # ----------------------------------------------------

        tool_calls = getattr(
            message,
            "tool_calls",
            None,
        )

        if tool_calls:

            return tool_calls

        # ----------------------------------------------------
        # NORMAL TEXT RESPONSE
        # ----------------------------------------------------

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
# SAFE OUTPUT HELPER
# ============================================================

def get_output_text(result) -> str:
    """
    Convert CrewAI CrewOutput / TaskOutput / normal values
    into plain text.
    """

    if result is None:
        return ""

    # CrewOutput.raw
    raw = getattr(
        result,
        "raw",
        None,
    )

    if raw is not None:
        return str(raw)

    # TaskOutput.raw
    output = getattr(
        result,
        "output",
        None,
    )

    if output is not None:
        return str(output)

    return str(result)


# ============================================================
# STATUS CALLBACK HELPER
# ============================================================

def update_status(
    status_callback,
    key: str,
    message: str,
):
    """
    Safely update Streamlit UI status if a callback
    was provided by app.py.
    """

    if status_callback is None:
        return

    try:
        status_callback(
            key,
            message,
        )
    except Exception:
        # UI callbacks should never crash research execution.
        pass


# ============================================================
# MAIN RESEARCH FUNCTION
# ============================================================

def run_research(
    research_question: str,
    status_callback=None,
):
    """
    Run the complete multi-agent research pipeline.

    Pipeline:

        Research Manager
              ↓
        ┌─────┼─────────────┐
        ↓     ↓             ↓
       Web  Academic    Industry
        └─────┼─────────────┘
              ↓
          Synthesizer
              ↓
          Final Report
    """

    if not research_question:
        raise ValueError(
            "Please provide a research question."
        )

    research_question = research_question.strip()

    if not research_question:
        raise ValueError(
            "Please provide a research question."
        )

    # ========================================================
    # CREATE LLM
    # ========================================================

    llm = create_llm()

    # ========================================================
    # CREATE AGENTS
    # ========================================================

    manager = create_research_manager(
        llm=llm
    )

    web_researcher = create_web_researcher(
        llm=llm
    )

    academic_researcher = create_academic_researcher(
        llm=llm
    )

    industry_researcher = create_industry_researcher(
        llm=llm
    )

    synthesizer = create_synthesizer(
        llm=llm
    )

    # ========================================================
    # 1. RESEARCH MANAGER
    # ========================================================

    update_status(
        status_callback,
        "manager",
        "Creating research strategy...",
    )

    manager_task = Task(
        description=f"""
You are managing a multi-agent research project.

Research question:

{research_question}

Your job is to create a clear research plan for the
specialist researchers.

Create a plan containing:

1. The main research objective.
2. Key questions that must be answered.
3. Important concepts or terminology to investigate.
4. What evidence should be collected.
5. What should be investigated by:
   - Web Researcher
   - Academic Researcher
   - Industry / Market Researcher
6. Important risks, assumptions, or limitations.

Do NOT write the final research report.

Your output should be a concise but detailed research plan
that the three specialist researchers can directly follow.
""",
        expected_output="""
A structured research plan with:

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
    # 2. SPECIALIST RESEARCH
    # ========================================================

    update_status(
        status_callback,
        "web",
        "Web researcher started...",
    )

    update_status(
        status_callback,
        "academic",
        "Academic researcher started...",
    )

    update_status(
        status_callback,
        "industry",
        "Industry researcher started...",
    )

    # ========================================================
    # WEB RESEARCH TASK
    # ========================================================

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
        async_execution=True,
    )

    # ========================================================
    # ACADEMIC RESEARCH TASK
    # ========================================================

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
        async_execution=True,
    )

    # ========================================================
    # INDUSTRY RESEARCH TASK
    # ========================================================

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
        async_execution=True,
    )

    # ========================================================
    # RUN THREE SPECIALISTS
    #
    # CrewAI async tasks execute concurrently within this
    # specialist crew.
    # ========================================================

    specialist_crew = Crew(
        agents=[
            web_researcher,
            academic_researcher,
            industry_researcher,
        ],
        tasks=[
            web_task,
            academic_task,
            industry_task,
        ],
        process=Process.sequential,
        verbose=False,
    )

    specialist_result = specialist_crew.kickoff()

    # ========================================================
    # GET INDIVIDUAL RESULTS
    # ========================================================

    web_findings = get_output_text(
        getattr(
            web_task,
            "output",
            None,
        )
    )

    academic_findings = get_output_text(
        getattr(
            academic_task,
            "output",
            None,
        )
    )

    industry_findings = get_output_text(
        getattr(
            industry_task,
            "output",
            None,
        )
    )

    # Fallback if CrewAI did not attach task outputs
    # individually for some reason.
    if not web_findings:
        web_findings = get_output_text(
            specialist_result
        )

    if not academic_findings:
        academic_findings = (
            "Academic research output was not "
            "returned separately."
        )

    if not industry_findings:
        industry_findings = (
            "Industry research output was not "
            "returned separately."
        )

    update_status(
        status_callback,
        "web",
        "Web research completed.",
    )

    update_status(
        status_callback,
        "academic",
        "Academic research completed.",
    )

    update_status(
        status_callback,
        "industry",
        "Industry research completed.",
    )

    # ========================================================
    # 3. SYNTHESIZER
    # ========================================================

    update_status(
        status_callback,
        "synthesizer",
        "Synthesizing final report...",
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
REPORT REQUIREMENTS
========================================================

Create a professional research report.

Use this structure:

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

8. Do not mention internal agent names or the multi-agent
   implementation in the final report.

9. Do not say that you browsed the internet unless that
   is relevant to explaining the sources.

10. Make the report readable and professional.

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

    synthesis_result = synthesis_crew.kickoff()

    final_report = get_output_text(
        synthesis_result
    )

    update_status(
        status_callback,
        "synthesizer",
        "Final report completed.",
    )

    # ========================================================
    # RETURN COMPLETE RESULT
    # ========================================================

    return {
        "report": final_report,
        "research_plan": research_plan,
        "web_research": web_findings,
        "academic_research": academic_findings,
        "industry_research": industry_findings,
    }
