from crewai import Agent

from tools import (
    WebSearchTool,
    WebpageReaderTool,
)


def create_synthesizer(llm):

    return Agent(
        role="Research Synthesizer and Report Writer",

        goal=(
            "Combine the manager's research plan and the findings "
            "from the web, academic and industry researchers into "
            "one accurate, well-structured research report."
        ),

        backstory=(
            "You are a senior research analyst and professional "
            "report writer. You synthesize evidence from multiple "
            "research perspectives, resolve contradictions where "
            "possible, clearly distinguish evidence from interpretation, "
            "and never invent sources or facts."
        ),

        llm=llm,

        tools=[
            WebSearchTool(),
            WebpageReaderTool(),
        ],

        allow_delegation=False,

        max_iter=8,

        verbose=False,
    )
