import os
import socket
import ipaddress
from urllib.parse import urlparse

import requests
import streamlit as st
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field
from crewai.tools import BaseTool


# ============================================================
# SECRET HELPER
# ============================================================

def get_secret(name: str) -> str:
    """
    Works both locally and on Streamlit Cloud.
    """

    # Local environment variable
    value = os.getenv(name)

    if value:
        return value

    # Streamlit secrets
    try:
        return st.secrets[name]
    except Exception:
        return ""


# ============================================================
# WEB SEARCH TOOL
# ============================================================

class WebSearchInput(BaseModel):
    query: str = Field(
        ...,
        description="The web search query."
    )


class WebSearchTool(BaseTool):
    name: str = "Web Search"

    description: str = (
        "Search the public web for current information. "
        "Returns titles, URLs and snippets from search results."
    )

    args_schema: type[BaseModel] = WebSearchInput

    def _run(self, query: str) -> str:

        api_key = get_secret("SERPER_API_KEY")

        if not api_key:
            return (
                "ERROR: SERPER_API_KEY is not configured. "
                "Please add it to Streamlit secrets."
            )

        try:

            response = requests.post(
                "https://google.serper.dev/search",
                headers={
                    "X-API-KEY": api_key,
                    "Content-Type": "application/json",
                },
                json={
                    "q": query,
                    "num": 8,
                },
                timeout=30,
            )

            response.raise_for_status()

            data = response.json()

            results = data.get("organic", [])

            if not results:
                return "No web search results found."

            output = []

            for index, result in enumerate(results[:8], 1):

                output.append(
                    f"""
RESULT {index}

Title:
{result.get("title", "")}

URL:
{result.get("link", "")}

Snippet:
{result.get("snippet", "")}
""".strip()
                )

            return "\n\n---\n\n".join(output)

        except Exception as e:

            return f"Web search failed: {str(e)}"


# ============================================================
# ACADEMIC SEARCH TOOL
# ============================================================

class AcademicSearchInput(BaseModel):
    query: str = Field(
        ...,
        description="Academic research topic or question."
    )


def reconstruct_abstract(inverted_index):
    """
    OpenAlex stores some abstracts as an inverted index.
    Convert it back into readable text.
    """

    if not inverted_index:
        return ""

    words = []

    for word, positions in inverted_index.items():

        for position in positions:

            words.append((position, word))

    words.sort(key=lambda x: x[0])

    return " ".join(word for _, word in words)


class AcademicSearchTool(BaseTool):
    name: str = "Academic Search"

    description: str = (
        "Search OpenAlex for scholarly papers, academic studies, "
        "authors, publication dates, abstracts and citation counts."
    )

    args_schema: type[BaseModel] = AcademicSearchInput

    def _run(self, query: str) -> str:

        try:

            response = requests.get(
                "https://api.openalex.org/works",
                params={
                    "search": query,
                    "per-page": 10,
                },
                timeout=30,
            )

            response.raise_for_status()

            data = response.json()

            works = data.get("results", [])

            if not works:
                return "No academic papers found."

            output = []

            for index, work in enumerate(works[:10], 1):

                title = work.get("title", "Unknown title")

                publication_year = work.get(
                    "publication_year",
                    "Unknown"
                )

                cited_by = work.get(
                    "cited_by_count",
                    0
                )

                doi = work.get("doi")

                primary_location = work.get(
                    "primary_location"
                ) or {}

                landing_page = primary_location.get(
                    "landing_page_url"
                )

                abstract = reconstruct_abstract(
                    work.get("abstract_inverted_index")
                )

                if not abstract:
                    abstract = "Abstract not available."

                abstract = abstract[:3000]

                output.append(
                    f"""
PAPER {index}

Title:
{title}

Publication Year:
{publication_year}

Citations:
{cited_by}

DOI:
{doi or "Not available"}

URL:
{landing_page or "Not available"}

Abstract:
{abstract}
""".strip()
                )

            return "\n\n====================\n\n".join(output)

        except Exception as e:

            return f"Academic search failed: {str(e)}"


# ============================================================
# WEBPAGE READER
# ============================================================

class WebpageReaderInput(BaseModel):
    url: str = Field(
        ...,
        description="The public webpage URL to read."
    )


def is_safe_public_url(url: str) -> bool:

    try:

        parsed = urlparse(url)

        if parsed.scheme not in {"http", "https"}:
            return False

        hostname = parsed.hostname

        if not hostname:
            return False

        hostname_lower = hostname.lower()

        blocked_names = {
            "localhost",
            "localhost.localdomain",
        }

        if hostname_lower in blocked_names:
            return False

        # Direct IP validation
        try:

            ip = ipaddress.ip_address(hostname)

            if (
                ip.is_private
                or ip.is_loopback
                or ip.is_link_local
                or ip.is_reserved
                or ip.is_multicast
            ):
                return False

        except ValueError:

            # Domain name - resolve it
            try:

                resolved = socket.gethostbyname(hostname)

                ip = ipaddress.ip_address(resolved)

                if (
                    ip.is_private
                    or ip.is_loopback
                    or ip.is_link_local
                    or ip.is_reserved
                    or ip.is_multicast
                ):
                    return False

            except Exception:
                pass

        return True

    except Exception:

        return False


class WebpageReaderTool(BaseTool):
    name: str = "Read Webpage"

    description: str = (
        "Read the public text of an important webpage. "
        "Use this after finding a useful source in web search."
    )

    args_schema: type[BaseModel] = WebpageReaderInput

    def _run(self, url: str) -> str:

        if not is_safe_public_url(url):

            return "ERROR: URL is not a safe public webpage."

        try:

            response = requests.get(
                url,
                timeout=30,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 "
                        "(Research Multi Agent)"
                    )
                },
            )

            response.raise_for_status()

            soup = BeautifulSoup(
                response.text,
                "html.parser"
            )

            # Remove unnecessary page elements
            for element in soup(
                [
                    "script",
                    "style",
                    "noscript",
                    "svg",
                    "nav",
                    "footer",
                    "header",
                ]
            ):

                element.decompose()

            text = soup.get_text(
                separator=" ",
                strip=True
            )

            if not text:

                return "No readable text found."

            # Keep prompts manageable
            return text[:18000]

        except Exception as e:

            return f"Could not read webpage: {str(e)}"
