from crewai import Agent

from tools import (
    AcademicSearchTool,
    WebpageReaderTool,
)


def create_academic_researcher(llm):

    return Agent(
        role="Academic Research Specialist",

        goal=(
            "Investigate the research question through scholarly "
            "literature, academic studies, research papers and "
            "evidence from reputable researchers."
        ),

        backstory=(
            "You are an academic research specialist. "
            "You focus on peer-reviewed and scholarly evidence, "
            "identify important findings, compare studies and "
            "clearly communicate the strength and limitations "
            "of academic evidence."
        ),

        llm=llm,

        tools=[
            AcademicSearchTool(),
            WebpageReaderTool(),
        ],

        allow_delegation=False,

        max_iter=8,

        verbose=False,
    )
