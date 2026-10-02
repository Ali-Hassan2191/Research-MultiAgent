# crew.py

import os
import re
import time
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

TEMPERATURE = 0.2

# Keep retries low.
# A failed request should NOT create many extra API calls.
MAX_RETRIES = 2

# Maximum generated tokens per LLM request.
MAX_OUTPUT_TOKENS = 1200

# Keep context small for the 8K TPM limit.
MAX_RESEARCH_PLAN_CHARS = 3000
MAX_WEB_FINDINGS_CHARS = 5000
MAX_ACADEMIC_FINDINGS_CHARS = 5000
MAX_INDUSTRY_FINDINGS_CHARS = 5000

# Small pause between agents.
BETWEEN_AGENT_DELAY = 5


# ============================================================
# SECRET HELPER
# ============================================================

def get_secret(name: str) -> str:

    value = os.getenv(name)

    if value:
        return str(value)

    try:
        value = st.secrets[name]

        if value:
            return str(value)

    except Exception:
        pass

    return ""


# ============================================================
# TEXT LIMIT HELPER
# ============================================================

def limit_text(
    text: Any,
    max_chars: int,
) -> str:

    if text is None:
        return ""

    text = str(text).strip()

    if len(text) <= max_chars:
        return text

    return (
        text[:max_chars]
        + "\n\n[Content truncated to control token usage.]"
    )


# ============================================================
# GROQ LLM
# ============================================================

class GroqCrewLLM(BaseLLM):

    def __init__(
        self,
        model: str = MODEL_NAME,
        temperature: float = TEMPERATURE,
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

    # ========================================================
    # CLEAN VALUES
    # ========================================================

    def _clean_value(self, value):

        if isinstance(value, dict):

            cleaned = {}

            for key, item in value.items():

                # CrewAI may add this field.
                # Groq does not accept it.
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

    # ========================================================
    # CLEAN MESSAGES
    # ========================================================

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

                role = getattr(
                    message,
                    "role",
                    "user",
                )

                content = getattr(
                    message,
                    "content",
                    "",
                )

                cleaned_message = {
                    "role": role,
                    "content": self._clean_value(
                        content
                    ),
                }

                tool_calls = getattr(
                    message,
                    "tool_calls",
                    None,
                )

                if tool_calls:

                    cleaned_message["tool_calls"] = (
                        self._clean_value(tool_calls)
                    )

                name = getattr(
                    message,
                    "name",
                    None,
                )

                if name:
                    cleaned_message["name"] = name

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

    # ========================================================
    # EXTRACT RETRY WAIT
    # ========================================================

    def _get_retry_wait(self, error_text: str, attempt: int) -> int:

        # Try to extract:
        #
        # "try again in 19.6s"
        #
        # from Groq's error message.

        patterns = [
            r"try again in\s+([\d.]+)s",
            r"retry.*?([\d.]+)s",
            r"after\s+([\d.]+)s",
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                error_text,
                re.IGNORECASE,
            )

            if match:

                try:

                    seconds = float(
                        match.group(1)
                    )

                    # Add a small safety buffer.
                    return max(
                        5,
                        min(
                            int(seconds) + 2,
                            60,
                        ),
                    )

                except Exception:
                    pass

        # Fallback:
        # 8s -> 16s
        return min(
            8 * (2 ** attempt),
            30,
        )

    # ========================================================
    # GROQ CALL
    # ========================================================

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

            # Important for controlling output token usage.
            "max_tokens": MAX_OUTPUT_TOKENS,
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
        # RETRIES
        # ----------------------------------------------------

        for attempt in range(MAX_RETRIES):

            try:

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

                # CrewAI needs native tool calls
                # when the agent requests a tool.

                tool_calls = getattr(
                    message,
                    "tool_calls",
                    None,
                )

                if tool_calls:

                    return tool_calls

                return (
                    message.content
                    or ""
                )

            except Exception as exc:

                error_text = str(exc)

                is_rate_limit = (
                    "429" in error_text
                    or "rate_limit_exceeded" in error_text
                    or "Rate limit" in error_text
                    or "rate limit" in error_text
                )

                if not is_rate_limit:

                    raise

                # Do not keep retrying indefinitely.
                if attempt >= MAX_RETRIES - 1:

                    raise RuntimeError(
                        "Groq rate limit was reached "
                        "after the maximum number of retries. "
                        f"Original error: {error_text}"
                    ) from exc

                wait_time = self._get_retry_wait(
                    error_text,
                    attempt,
                )

                time.sleep(
                    wait_time
                )

        raise RuntimeError(
            "Groq request failed."
        )

    # ========================================================
    # CREWAI CAPABILITIES
    # ========================================================

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
        temperature=TEMPERATURE,
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
        pass


# ============================================================
# MANAGER
# ============================================================

def run_manager(
    research_question: str,
    status_callback=None,
):

    update_status(
        status_callback,
        "manager",
        "Research Manager is creating the plan...",
    )

    llm = create_llm()

    manager = create_research_manager(
        llm=llm
    )

    task = Task(
        description=f"""
Create a SHORT research plan for:

{research_question}

Include:

1. Main objective
2. 3 key research questions
3. Web evidence needed
4. Academic evidence needed
5. Industry evidence needed
6. Main limitations

Keep it under 500 words.

Do not write the final report.
""",
        expected_output="""
A short research plan with objective,
key questions, evidence requirements,
and limitations.
""",
        agent=manager,
    )

    crew = Crew(
        agents=[manager],
        tasks=[task],
        process=Process.sequential,
        verbose=False,
    )

    result = crew.kickoff()

    plan = limit_text(
        get_output_text(result),
        MAX_RESEARCH_PLAN_CHARS,
    )

    update_status(
        status_callback,
        "manager",
        "Research plan completed.",
    )

    return plan


# ============================================================
# WEB RESEARCH
# ============================================================

def run_web_research(
    research_question: str,
    research_plan: str,
    status_callback=None,
):

    update_status(
        status_callback,
        "web",
        "Web researcher is working...",
    )

    llm = create_llm()

    agent = create_web_researcher(
        llm=llm
    )

    research_plan = limit_text(
        research_plan,
        MAX_RESEARCH_PLAN_CHARS,
    )

    task = Task(
        description=f"""
Research this question:

{research_question}

Research plan:

{research_plan}

Use web search and webpage-reading tools.

Find only the most important current evidence.

Return:

- 3 to 4 key findings
- supporting facts
- source names
- source URLs
- important statistics if available

Keep the answer concise.

Do not invent facts or sources.
""",
        expected_output="""
3 to 4 concise web findings with
supporting sources and URLs.
""",
        agent=agent,
    )

    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=False,
    )

    result = crew.kickoff()

    findings = limit_text(
        get_output_text(result),
        MAX_WEB_FINDINGS_CHARS,
    )

    update_status(
        status_callback,
        "web",
        "Web research completed.",
    )

    return findings


# ============================================================
# ACADEMIC RESEARCH
# ============================================================

def run_academic_research(
    research_question: str,
    research_plan: str,
    status_callback=None,
):

    update_status(
        status_callback,
        "academic",
        "Academic researcher is working...",
    )

    llm = create_llm()

    agent = create_academic_researcher(
        llm=llm
    )

    research_plan = limit_text(
        research_plan,
        MAX_RESEARCH_PLAN_CHARS,
    )

    task = Task(
        description=f"""
Research this question:

{research_question}

Research plan:

{research_plan}

Use academic search tools.

Find the most relevant scholarly evidence.

Return:

- 3 important papers
- title
- authors when available
- year
- key finding
- DOI or URL when available
- important limitation

Keep the answer concise.

Do not invent papers or citations.
""",
        expected_output="""
3 concise academic findings with
paper information and source links.
""",
        agent=agent,
    )

    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=False,
    )

    result = crew.kickoff()

    findings = limit_text(
        get_output_text(result),
        MAX_ACADEMIC_FINDINGS_CHARS,
    )

    update_status(
        status_callback,
        "academic",
        "Academic research completed.",
    )

    return findings


# ============================================================
# INDUSTRY RESEARCH
# ============================================================

def run_industry_research(
    research_question: str,
    research_plan: str,
    status_callback=None,
):

    update_status(
        status_callback,
        "industry",
        "Industry researcher is working...",
    )

    llm = create_llm()

    agent = create_industry_researcher(
        llm=llm
    )

    research_plan = limit_text(
        research_plan,
        MAX_RESEARCH_PLAN_CHARS,
    )

    task = Task(
        description=f"""
Research the industry and market side of:

{research_question}

Research plan:

{research_plan}

Use web research tools.

Focus only on the most relevant:

- industry trends
- companies
- products
- adoption
- market developments
- practical applications
- business models
- risks

Return:

- 3 to 4 key findings
- evidence
- source names
- source URLs

Keep the answer concise.

Do not invent statistics or company claims.
""",
        expected_output="""
3 to 4 concise industry findings
with evidence and source URLs.
""",
        agent=agent,
    )

    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=False,
    )

    result = crew.kickoff()

    findings = limit_text(
        get_output_text(result),
        MAX_INDUSTRY_FINDINGS_CHARS,
    )

    update_status(
        status_callback,
        "industry",
        "Industry research completed.",
    )

    return findings


# ============================================================
# SYNTHESIZER
# ============================================================

def run_synthesis(
    research_question: str,
    research_plan: str,
    web_findings: str,
    academic_findings: str,
    industry_findings: str,
    status_callback=None,
):

    update_status(
        status_callback,
        "synthesizer",
        "Synthesizer is writing the final report...",
    )

    llm = create_llm()

    agent = create_synthesizer(
        llm=llm
    )

    # Strictly limit everything entering synthesis.
    research_plan = limit_text(
        research_plan,
        MAX_RESEARCH_PLAN_CHARS,
    )

    web_findings = limit_text(
        web_findings,
        MAX_WEB_FINDINGS_CHARS,
    )

    academic_findings = limit_text(
        academic_findings,
        MAX_ACADEMIC_FINDINGS_CHARS,
    )

    industry_findings = limit_text(
        industry_findings,
        MAX_INDUSTRY_FINDINGS_CHARS,
    )

    task = Task(
        description=f"""
Write a concise research report about:

{research_question}

RESEARCH PLAN:

{research_plan}

WEB FINDINGS:

{web_findings}

ACADEMIC FINDINGS:

{academic_findings}

INDUSTRY FINDINGS:

{industry_findings}

Use this structure:

# Executive Summary

# Key Findings

# Academic Evidence

# Industry / Market Evidence

# Cross-Source Analysis

# Limitations

# Conclusion

# Sources

Rules:

- Use only the supplied research.
- Do not invent facts.
- Do not invent citations.
- Preserve source URLs.
- Distinguish evidence from interpretation.
- Mention conflicts between sources when present.
- Keep the report concise.
""",
        expected_output="""
A concise evidence-based research report
with findings, analysis, limitations,
conclusion, and sources.
""",
        agent=agent,
    )

    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=False,
    )

    result = crew.kickoff()

    final_report = get_output_text(
        result
    )

    update_status(
        status_callback,
        "synthesizer",
        "Final report completed.",
    )

    return final_report


# ============================================================
# MAIN RESEARCH PIPELINE
# ============================================================

def run_research(
    research_question: str,
    status_callback=None,
):

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
    # 1. MANAGER
    # ========================================================

    research_plan = run_manager(
        research_question,
        status_callback,
    )

    # ========================================================
    # 2. WEB
    # ========================================================

    web_findings = run_web_research(
        research_question,
        research_plan,
        status_callback,
    )

    time.sleep(
        BETWEEN_AGENT_DELAY
    )

    # ========================================================
    # 3. ACADEMIC
    # ========================================================

    academic_findings = run_academic_research(
        research_question,
        research_plan,
        status_callback,
    )

    time.sleep(
        BETWEEN_AGENT_DELAY
    )

    # ========================================================
    # 4. INDUSTRY
    # ========================================================

    industry_findings = run_industry_research(
        research_question,
        research_plan,
        status_callback,
    )

    time.sleep(
        BETWEEN_AGENT_DELAY
    )

    # ========================================================
    # 5. SYNTHESIS
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
    # FINAL RESULT
    # ========================================================

    return {
        "report": final_report,

        "research_plan": research_plan,

        "web_research": web_findings,

        "academic_research": academic_findings,

        "industry_research": industry_findings,
    }
