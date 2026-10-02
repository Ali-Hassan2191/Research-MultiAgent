from crewai import Agent

from tools import (
    WebSearchTool,
    WebpageReaderTool,
)


def create_industry_researcher(llm):

    return Agent(
        role="Industry and Market Research Specialist",

        goal=(
            "Investigate the practical industry, business, market, "
            "technology and competitive implications of the research "
            "question."
        ),

        backstory=(
            "You are an industry and market research analyst. "
            "You investigate companies, products, market movements, "
            "business models, adoption patterns, competitive dynamics "
            "and practical implications using credible sources."
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
