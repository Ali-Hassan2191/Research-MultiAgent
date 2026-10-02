from crewai import Agent

from tools import WebSearchTool


def create_research_manager(llm):

    return Agent(
        role="Research Manager",

        goal=(
            "Turn the user's research question into a clear research "
            "plan covering web evidence, academic evidence and "
            "industry or market evidence."
        ),

        backstory=(
            "You are an experienced research manager. "
            "You break complicated questions into focused research "
            "directions and make sure different research specialists "
            "investigate complementary aspects of the problem."
        ),

        llm=llm,

        tools=[
            WebSearchTool()
        ],

        allow_delegation=False,

        max_iter=6,

        verbose=False,
    )
