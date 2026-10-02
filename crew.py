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
# CONFIG
# ============================================================

MODEL_NAME = "openai/gpt-oss-120b"


def get_secret(name: str) -> str:
    """Get a secret from environment variables or Streamlit secrets."""

    value = os.getenv(name)

    if value:
        return value

    try:
        return st.secrets[name]
    except Exception:
        return ""


# ============================================================
# CUSTOM GROQ LLM FOR CREWAI
# ============================================================

class GroqCrewLLM(BaseLLM):
    """
    CrewAI-compatible LLM that talks directly to Groq.

    This avoids CrewAI's custom_openai model-name rewriting,
    which would turn:

        openai/gpt-oss-120b

    into:

        gpt-oss-120b

    Groq requires the full model ID.
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
                "Add it to Streamlit Cloud Secrets."
            )

        self.client = Groq(
            api_key=api_key,
        )

    def call(
        self,
        messages,
        tools=None,
        callbacks=None,
        available_functions=None,
        **kwargs,
    ) -> Any:

        # Convert a single string into a message list.
        if isinstance(messages, str):
            messages = [
                {
                    "role": "user",
                    "content": messages,
                }
            ]

        # Make a normal Python list.
        clean_messages = []

        for message in messages:

            if isinstance(message, dict):

                clean_messages.append(message)

            else:

                # Defensive conversion for CrewAI message objects.
                try:
                    clean_messages.append(
                        {
                            "role": message.role,
                            "content": message.content,
                        }
                    )
                except Exception:

                    clean_messages.append(
                        {
                            "role": "user",
                            "content": str(message),
                        }
                    )

        request_kwargs = {
            "model": self.model,
            "messages": clean_messages,
            "temperature": self.temperature,
        }

        # CrewAI converts its tools into OpenAI-compatible schemas.
        if tools:

            request_kwargs["tools"] = tools
            request_kwargs["tool_choice"] = "auto"

        # Send request directly to Groq.
        response = self.client.chat.completions.create(
            **request_kwargs
        )

        message = response.choices[0].message

        # ----------------------------------------------------
        # TOOL CALL
        # ----------------------------------------------------

        if getattr(message, "tool_calls", None):

            return message.tool_calls

        # ----------------------------------------------------
        # NORMAL RESPONSE
        # ----------------------------------------------------

        return message.content or ""

    def supports_function_calling(self) -> bool:
        """
        GPT-OSS 120B supports tool/function calling on Groq.
        """
        return True

    def supports_stop_words(self) -> bool:
        """
        We don't explicitly send CrewAI stop words to Groq.
        """
        return False

    def get_context_window_size(self) -> int:
        """
        Groq lists GPT-OSS 120B with a 131,072-token context window.
        """
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
# MAIN RESEARCH PIPELINE
# ============================================================

def run_research(
    research_question: str,
    status_callback=None,
):

    if not research_question.strip():

        raise ValueError(
            "Research question cannot be empty."
        )

    llm = create_llm()

    # ========================================================
    # CREATE AGENTS
    # ========================================================

    manager = create_research_manager(llm)

    web_researcher = create_web_researcher(llm)

    academic_researcher = create_academic_researcher(llm)

    industry_researcher = create_industry_researcher(llm)

    synthesizer = create_synthesizer(llm)


    # ========================================================
    # STAGE 1 — RESEARCH MANAGER
    # ========================================================

    if status_callback:

        status_callback(
            "manager",
            "running",
            "🧭 Research Manager — planning research",
        )


    manager_task = Task(
        description=f"""
        Develop a focused research plan for this question:

        {research_question}

        The plan must identify:

        1. The main questions that need to be answered.
        2. Important concepts and terminology.
        3. What should be investigated on the public web.
        4. What academic evidence should be investigated.
        5. What industry and market evidence should be investigated.
        6. Important limitations or uncertainties.

        Keep the plan practical and focused.
        """,

        expected_output="""
        A concise research plan containing:
        - Research objectives
        - Key questions
        - Web research focus
        - Academic research focus
        - Industry research focus
        - Important limitations
        """,

        agent=manager,
    )


    manager_crew = Crew(
        agents=[manager],

        tasks=[manager_task],

        process=Process.sequential,

        verbose=False,
    )


    manager_result = manager_crew.kickoff()

    research_plan = manager_result.raw


    if status_callback:

        status_callback(
            "manager",
            "complete",
            "✓ Research Manager — plan completed",
        )


    # ========================================================
    # STAGE 2 — THREE PARALLEL RESEARCH AGENTS
    # ========================================================

    if status_callback:

        status_callback(
            "web",
            "running",
            "🌐 Web Research — working",
        )

        status_callback(
            "academic",
            "running",
            "🎓 Academic Research — working",
        )

        status_callback(
            "industry",
            "running",
            "📊 Industry Research — working",
        )


    # --------------------------------------------------------
    # WEB
    # --------------------------------------------------------

    web_task = Task(
        description=f"""
        Research the following question from current public
        web sources:

        {research_question}

        Research plan:

        {research_plan}

        Use your web research tools.

        Find:
        - Current facts
        - Recent developments
        - Important organizations
        - Relevant statistics
        - Industry announcements
        - High-quality primary sources

        Whenever possible, prefer primary or authoritative sources.

        Include source URLs in your findings.
        """,

        expected_output="""
        A structured web research report containing:
        - Key findings
        - Evidence
        - Important dates
        - Relevant statistics
        - Source URLs
        - Uncertainties
        """,

        agent=web_researcher,

        async_execution=True,
    )


    # --------------------------------------------------------
    # ACADEMIC
    # --------------------------------------------------------

    academic_task = Task(
        description=f"""
        Investigate the following research question using
        academic and scholarly sources:

        {research_question}

        Research plan:

        {research_plan}

        Use the academic research tools.

        Focus on:
        - Peer-reviewed research
        - Scholarly publications
        - Research findings
        - Methods
        - Evidence
        - Publication dates
        - Citation information where available

        Clearly distinguish established findings from
        preliminary or limited evidence.

        Include source URLs or identifiers whenever available.
        """,

        expected_output="""
        A structured academic research report containing:
        - Major academic findings
        - Evidence
        - Relevant studies
        - Publication information
        - Limitations
        - Source URLs or identifiers
        """,

        agent=academic_researcher,

        async_execution=True,
    )


    # --------------------------------------------------------
    # INDUSTRY
    # --------------------------------------------------------

    industry_task = Task(
        description=f"""
        Analyze the industry and market dimensions of:

        {research_question}

        Research plan:

        {research_plan}

        Use web research tools to investigate:

        - Companies
        - Products
        - Market developments
        - Business models
        - Commercial adoption
        - Competitive landscape
        - Investment or funding signals
        - Industry challenges
        - Market opportunities

        Clearly distinguish reported facts from estimates
        and company claims.

        Include source URLs.
        """,

        expected_output="""
        A structured industry research report containing:
        - Market findings
        - Company examples
        - Competitive developments
        - Business implications
        - Industry challenges
        - Source URLs
        """,

        agent=industry_researcher,

        async_execution=True,
    )


    research_crew = Crew(
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


    research_result = research_crew.kickoff()


    # ========================================================
    # EXTRACT RESEARCH RESULTS
    # ========================================================

    research_outputs = []

    for task_output in research_result.tasks_output:

        try:
            research_outputs.append(
                task_output.raw
            )
        except Exception:

            research_outputs.append(
                str(task_output)
            )


    # We expect three outputs.
    web_findings = (
        research_outputs[0]
        if len(research_outputs) > 0
        else ""
    )

    academic_findings = (
        research_outputs[1]
        if len(research_outputs) > 1
        else ""
    )

    industry_findings = (
        research_outputs[2]
        if len(research_outputs) > 2
        else ""
    )


    if status_callback:

        status_callback(
            "web",
            "complete",
            "✓ Web Research — completed",
        )

        status_callback(
            "academic",
            "complete",
            "✓ Academic Research — completed",
        )

        status_callback(
            "industry",
            "complete",
            "✓ Industry Research — completed",
        )


    # ========================================================
    # STAGE 3 — SYNTHESIZER
    # ========================================================

    if status_callback:

        status_callback(
            "synthesizer",
            "running",
            "✍️ Synthesizer — writing final report",
        )


    synthesis_task = Task(
        description=f"""
        Create a high-quality final research report.

        ORIGINAL QUESTION
        ==================
        {research_question}


        RESEARCH PLAN
        ==================
        {research_plan}


        WEB RESEARCH
        ==================
        {web_findings}


        ACADEMIC RESEARCH
        ==================
        {academic_findings}


        INDUSTRY / MARKET RESEARCH
        ==================
        {industry_findings}


        Your job is to synthesize the evidence.

        Do not simply copy the research outputs.

        Compare findings across the three perspectives.

        Clearly distinguish:
        - Established evidence
        - Reported claims
        - Estimates
        - Conflicting evidence
        - Important uncertainty

        Do not invent sources, statistics, quotations,
        companies, studies, or citations.

        Preserve useful source URLs from the research.

        Produce a polished report suitable for a researcher,
        student, analyst, or business professional.
        """,

        expected_output="""
        A complete Markdown research report with these sections:

        # Executive Summary

        # Key Findings

        # Web Research Findings

        # Academic Evidence

        # Industry / Market Evidence

        # Cross-Source Analysis

        # Limitations and Uncertainties

        # Conclusion

        # Sources
        """,

        agent=synthesizer,
    )


    synthesis_crew = Crew(
        agents=[synthesizer],

        tasks=[synthesis_task],

        process=Process.sequential,

        verbose=False,
    )


    synthesis_result = synthesis_crew.kickoff()

    final_report = synthesis_result.raw


    if status_callback:

        status_callback(
            "synthesizer",
            "complete",
            "✓ Synthesizer — report completed",
        )


    # ========================================================
    # RETURN
    # ========================================================

    return {
        "report": final_report,
        "research_plan": research_plan,
        "web_research": web_findings,
        "academic_research": academic_findings,
        "industry_research": industry_findings,
    }
