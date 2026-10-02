from crewai import Agent

from tools import (
    WebSearchTool,
    WebpageReaderTool,
)


def create_web_researcher(llm):

    return Agent(
        role="Web Research Specialist",

        goal=(
            "Investigate the research question using current and "
            "reliable web sources. Find concrete facts, recent "
            "developments, primary sources and useful evidence."
        ),

        backstory=(
            "You are a professional web researcher. "
            "You search broadly, identify credible sources, "
            "open important pages and distinguish useful evidence "
            "from weak or repetitive information."
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
