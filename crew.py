import os

from crewai import (
    Agent,
    Crew,
    LLM,
    Process,
    Task,
)

from tools import get_secret

from research_manager import create_research_manager
from web_researcher import create_web_researcher
from academic_researcher import create_academic_researcher
from industry_researcher import create_industry_researcher
from synthesizer import create_synthesizer


# ============================================================
# LLM
# ============================================================

def create_llm():

    groq_api_key = get_secret("GROQ_API_KEY")

    if not groq_api_key:

        raise ValueError(
            "GROQ_API_KEY is missing. "
            "Add it to Streamlit Secrets."
        )

    return LLM(
        model="openai/gpt-oss-120b",

        custom_openai=True,

        base_url="https://api.groq.com/openai/v1",

        api_key=groq_api_key,

        temperature=0.2,
    )


# ============================================================
# MAIN RESEARCH PIPELINE
# ============================================================

def run_research(
    research_question: str,
    status_callback=None,
):
    """
    Runs:

    1. Research Manager
    2. Web Research
    3. Academic Research
    4. Industry Research
    5. Synthesizer
    """

    if not research_question.strip():

        raise ValueError(
            "Research question cannot be empty."
        )

    llm = create_llm()

    # --------------------------------------------------------
    # AGENTS
    # --------------------------------------------------------

    manager = create_research_manager(llm)

    web_researcher = create_web_researcher(llm)

    academic_researcher = create_academic_researcher(llm)

    industry_researcher = create_industry_researcher(llm)

    synthesizer = create_synthesizer(llm)

    # ========================================================
    # STEP 1 — RESEARCH MANAGER
    # ========================================================

    if status_callback:

        status_callback(
            "manager",
            "running",
            "🧭 Research Manager — planning the investigation"
        )

    manager_task = Task(

        description=f"""
You are managing a research project.

Research question:

{research_question}

Create a focused research plan.

The plan must contain:

1. The core question to answer.
2. Important sub-questions.
3. What the Web Research Specialist should investigate.
4. What the Academic Research Specialist should investigate.
5. What the Industry and Market Research Specialist should investigate.
6. Important source types to prioritize.
7. Potential contradictions or evidence gaps to watch for.

Do not write the final report.
Create a practical research plan for the three specialists.
""",

        expected_output="""
A structured research plan with:
- Core question
- Web research directions
- Academic research directions
- Industry/market research directions
- Source priorities
- Evidence gaps
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
            "✓ Research Manager — research plan completed"
        )

    # ========================================================
    # STEP 2 — THREE PARALLEL RESEARCHERS
    # ========================================================

    if status_callback:

        status_callback(
            "web",
            "running",
            "🌐 Web Research — searching current sources"
        )

        status_callback(
            "academic",
            "running",
            "🎓 Academic Research — searching scholarly evidence"
        )

        status_callback(
            "industry",
            "running",
            "📊 Industry Research — analyzing market evidence"
        )

    # --------------------------------------------------------
    # WEB TASK
    # --------------------------------------------------------

    web_task = Task(

        description=f"""
Research the following question from the web:

{research_question}

Here is the research manager's plan:

{research_plan}

Your responsibilities:

- Search for current information.
- Find credible sources.
- Prefer primary sources where possible.
- Read important webpages.
- Extract concrete facts.
- Identify dates.
- Identify important organizations, products, technologies,
  events or developments.
- Record URLs for important sources.
- Avoid unsupported claims.

Produce a concise but evidence-rich research brief.
""",

        expected_output="""
A web research brief containing:

- Key findings
- Supporting evidence
- Important dates
- Important organizations or sources
- Source URLs
- Uncertainty or limitations
""",

        agent=web_researcher,

        async_execution=True,
    )

    # --------------------------------------------------------
    # ACADEMIC TASK
    # --------------------------------------------------------

    academic_task = Task(

        description=f"""
Research the following question using academic literature:

{research_question}

Here is the research manager's plan:

{research_plan}

Your responsibilities:

- Search scholarly literature.
- Identify important studies.
- Extract meaningful findings.
- Include publication years.
- Include authors or institutions when useful.
- Note citation information when available.
- Compare findings where appropriate.
- Identify limitations of studies.
- Include URLs or DOI information when available.

Do not invent academic evidence.
""",

        expected_output="""
An academic research brief containing:

- Important studies
- Main findings
- Publication years
- Authors/institutions
- Relevant URLs or DOI information
- Areas of agreement/disagreement
- Research limitations
""",

        agent=academic_researcher,

        async_execution=True,
    )

    # --------------------------------------------------------
    # INDUSTRY TASK
    # --------------------------------------------------------

    industry_task = Task(

        description=f"""
Research the following question from an industry and market
perspective:

{research_question}

Here is the research manager's plan:

{research_plan}

Investigate:

- Companies
- Products
- Market developments
- Business models
- Industry adoption
- Competitive dynamics
- Technology trends
- Commercial implications
- Relevant recent announcements
- Credible market evidence

Use web search and read important sources.

Record source URLs.

Do not make unsupported market claims.
""",

        expected_output="""
An industry and market research brief containing:

- Industry findings
- Market developments
- Companies/products
- Competitive information
- Adoption or business implications
- Supporting source URLs
- Important uncertainties
""",

        agent=industry_researcher,

        async_execution=True,
    )

    # --------------------------------------------------------
    # PARALLEL RESEARCH CREW
    # --------------------------------------------------------

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

    if status_callback:

        status_callback(
            "web",
            "complete",
            "✓ Web Research — completed"
        )

        status_callback(
            "academic",
            "complete",
            "✓ Academic Research — completed"
        )

        status_callback(
            "industry",
            "complete",
            "✓ Industry Research — completed"
        )

    # ========================================================
    # COLLECT RESEARCH OUTPUTS
    # ========================================================

    research_outputs = []

    for output in research_result.tasks_output:

        if output and output.raw:

            research_outputs.append(
                output.raw
            )

    combined_research = "\n\n".join(
        research_outputs
    )

    # ========================================================
    # STEP 3 — SYNTHESIS
    # ========================================================

    if status_callback:

        status_callback(
            "synthesizer",
            "running",
            "✍️ Synthesizer — writing the final research report"
        )

    synthesis_task = Task(

        description=f"""
Create the final research report for this question:

{research_question}

RESEARCH MANAGER PLAN
=====================

{research_plan}


RESEARCH FINDINGS
=================

{combined_research}


Your job is to synthesize these findings into one professional,
accurate research report.

IMPORTANT RULES:

1. Do not invent facts.
2. Do not invent citations.
3. Preserve source URLs supplied by researchers.
4. Clearly distinguish evidence from interpretation.
5. If sources disagree, explain the disagreement.
6. Prefer specific evidence over vague statements.
7. Mention important limitations.
8. Use Markdown.
9. Make the report useful to a human decision-maker.
10. Do not mention internal agent mechanics unless useful.

Use exactly this structure:

# Research Report

## Executive Summary

## Key Findings

## Web Research Findings

## Academic Evidence

## Industry and Market Evidence

## Cross-Source Analysis

## Important Limitations

## Conclusion

## Sources

Under Sources, provide a clean bullet list of the important
URLs found by the researchers.
""",

        expected_output="""
A polished Markdown research report containing:

- Executive Summary
- Key Findings
- Web Research Findings
- Academic Evidence
- Industry and Market Evidence
- Cross-Source Analysis
- Important Limitations
- Conclusion
- Sources
""",

        agent=synthesizer,
    )

    synthesis_crew = Crew(

        agents=[synthesizer],

        tasks=[synthesis_task],

        process=Process.sequential,

        verbose=False,
    )

    final_result = synthesis_crew.kickoff()

    final_report = final_result.raw

    if status_callback:

        status_callback(
            "synthesizer",
            "complete",
            "✓ Synthesizer — final report completed"
        )

    return {
        "research_plan": research_plan,
        "research": combined_research,
        "report": final_report,
    }
