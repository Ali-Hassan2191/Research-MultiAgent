# tools.py

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
# CONFIGURATION
# ============================================================

# Keep external tool output small.
MAX_WEB_RESULTS = 5
MAX_SNIPPET_CHARS = 500

MAX_ACADEMIC_RESULTS = 5
MAX_ABSTRACT_CHARS = 1000

MAX_WEBPAGE_CHARS = 3000

REQUEST_TIMEOUT = 20


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
        "Returns a small list of titles, URLs and snippets. "
        "Use this to find relevant sources."
    )

    args_schema: type[BaseModel] = WebSearchInput

    def _run(
        self,
        query: str,
    ) -> str:

        api_key = get_secret(
            "SERPER_API_KEY"
        )

        if not api_key:

            return (
                "ERROR: SERPER_API_KEY is not configured. "
                "Please add it to Streamlit secrets."
            )

        query = str(query).strip()

        if not query:

            return "ERROR: Search query is empty."

        try:

            response = requests.post(
                "https://google.serper.dev/search",

                headers={
                    "X-API-KEY": api_key,
                    "Content-Type": "application/json",
                },

                json={
                    "q": query,

                    # Reduced from 8 to 5.
                    "num": MAX_WEB_RESULTS,
                },

                timeout=REQUEST_TIMEOUT,
            )

            response.raise_for_status()

            data = response.json()

            results = data.get(
                "organic",
                [],
            )

            if not results:

                return (
                    "No web search results found."
                )

            output = []

            for index, result in enumerate(
                results[:MAX_WEB_RESULTS],
                1,
            ):

                title = str(
                    result.get(
                        "title",
                        "",
                    )
                ).strip()

                url = str(
                    result.get(
                        "link",
                        "",
                    )
                ).strip()

                snippet = str(
                    result.get(
                        "snippet",
                        "",
                    )
                ).strip()

                snippet = snippet[
                    :MAX_SNIPPET_CHARS
                ]

                output.append(
                    (
                        f"RESULT {index}\n\n"
                        f"Title:\n{title}\n\n"
                        f"URL:\n{url}\n\n"
                        f"Snippet:\n{snippet}"
                    )
                )

            return "\n\n---\n\n".join(
                output
            )

        except requests.RequestException as e:

            return (
                "Web search failed: "
                f"{str(e)}"
            )

        except Exception as e:

            return (
                "Web search failed: "
                f"{str(e)}"
            )


# ============================================================
# ACADEMIC SEARCH TOOL
# ============================================================

class AcademicSearchInput(BaseModel):

    query: str = Field(
        ...,
        description="Academic research topic or question."
    )


def reconstruct_abstract(
    inverted_index,
) -> str:

    if not inverted_index:

        return ""

    words = []

    try:

        for word, positions in (
            inverted_index.items()
        ):

            for position in positions:

                words.append(
                    (
                        position,
                        word,
                    )
                )

        words.sort(
            key=lambda x: x[0]
        )

        return " ".join(
            word
            for _, word in words
        )

    except Exception:

        return ""


class AcademicSearchTool(BaseTool):

    name: str = "Academic Search"

    description: str = (
        "Search OpenAlex for scholarly papers "
        "and return concise paper information."
    )

    args_schema: type[BaseModel] = AcademicSearchInput

    def _run(
        self,
        query: str,
    ) -> str:

        query = str(query).strip()

        if not query:

            return (
                "ERROR: Academic search query is empty."
            )

        try:

            response = requests.get(
                "https://api.openalex.org/works",

                params={
                    "search": query,

                    # Reduced from 10 to 5.
                    "per-page": MAX_ACADEMIC_RESULTS,
                },

                timeout=REQUEST_TIMEOUT,
            )

            response.raise_for_status()

            data = response.json()

            works = data.get(
                "results",
                [],
            )

            if not works:

                return (
                    "No academic papers found."
                )

            output = []

            for index, work in enumerate(
                works[:MAX_ACADEMIC_RESULTS],
                1,
            ):

                title = work.get(
                    "title",
                    "Unknown title",
                )

                publication_year = work.get(
                    "publication_year",
                    "Unknown",
                )

                cited_by = work.get(
                    "cited_by_count",
                    0,
                )

                doi = work.get(
                    "doi"
                )

                primary_location = (
                    work.get(
                        "primary_location"
                    )
                    or {}
                )

                landing_page = (
                    primary_location.get(
                        "landing_page_url"
                    )
                )

                abstract = reconstruct_abstract(
                    work.get(
                        "abstract_inverted_index"
                    )
                )

                if not abstract:

                    abstract = (
                        "Abstract not available."
                    )

                # Strongly reduced from 3000.
                abstract = abstract[
                    :MAX_ABSTRACT_CHARS
                ]

                # Get a simple author list.
                authorships = (
                    work.get(
                        "authorships"
                    )
                    or []
                )

                author_names = []

                for authorship in authorships[:5]:

                    author = (
                        authorship.get(
                            "author"
                        )
                        or {}
                    )

                    name = author.get(
                        "display_name"
                    )

                    if name:
                        author_names.append(
                            name
                        )

                authors = (
                    ", ".join(
                        author_names
                    )
                    if author_names
                    else "Not available"
                )

                output.append(
                    (
                        f"PAPER {index}\n\n"
                        f"Title:\n{title}\n\n"
                        f"Authors:\n{authors}\n\n"
                        f"Publication Year:\n"
                        f"{publication_year}\n\n"
                        f"Citations:\n{cited_by}\n\n"
                        f"DOI:\n"
                        f"{doi or 'Not available'}\n\n"
                        f"URL:\n"
                        f"{landing_page or 'Not available'}\n\n"
                        f"Abstract:\n{abstract}"
                    )
                )

            return "\n\n====================\n\n".join(
                output
            )

        except requests.RequestException as e:

            return (
                "Academic search failed: "
                f"{str(e)}"
            )

        except Exception as e:

            return (
                "Academic search failed: "
                f"{str(e)}"
            )


# ============================================================
# WEBPAGE READER
# ============================================================

class WebpageReaderInput(BaseModel):

    url: str = Field(
        ...,
        description="The public webpage URL to read."
    )


def is_safe_public_url(
    url: str,
) -> bool:

    try:

        parsed = urlparse(
            url
        )

        if parsed.scheme not in {
            "http",
            "https",
        }:

            return False

        hostname = parsed.hostname

        if not hostname:

            return False

        hostname_lower = (
            hostname.lower()
        )

        blocked_names = {
            "localhost",
            "localhost.localdomain",
        }

        if hostname_lower in blocked_names:

            return False

        # ----------------------------------------------------
        # Direct IP validation
        # ----------------------------------------------------

        try:

            ip = ipaddress.ip_address(
                hostname
            )

            if (
                ip.is_private
                or ip.is_loopback
                or ip.is_link_local
                or ip.is_reserved
                or ip.is_multicast
            ):

                return False

        except ValueError:

            # ------------------------------------------------
            # Domain name validation
            # ------------------------------------------------

            try:

                resolved = (
                    socket.gethostbyname(
                        hostname
                    )
                )

                ip = ipaddress.ip_address(
                    resolved
                )

                if (
                    ip.is_private
                    or ip.is_loopback
                    or ip.is_link_local
                    or ip.is_reserved
                    or ip.is_multicast
                ):

                    return False

            except Exception:

                # If DNS resolution fails,
                # requests will handle the error.
                pass

        return True

    except Exception:

        return False


class WebpageReaderTool(BaseTool):

    name: str = "Read Webpage"

    description: str = (
        "Read a small amount of useful text "
        "from an important public webpage. "
        "Use this after finding a useful source."
    )

    args_schema: type[BaseModel] = WebpageReaderInput

    def _run(
        self,
        url: str,
    ) -> str:

        url = str(url).strip()

        if not is_safe_public_url(
            url
        ):

            return (
                "ERROR: URL is not a safe public webpage."
            )

        try:

            response = requests.get(

                url,

                timeout=REQUEST_TIMEOUT,

                headers={
                    "User-Agent": (
                        "Mozilla/5.0 "
                        "(Research Multi Agent)"
                    )
                },
            )

            response.raise_for_status()

            # Don't process huge response bodies.
            # This prevents unnecessarily large memory
            # and parsing work.
            response_text = response.text[
                :100000
            ]

            soup = BeautifulSoup(
                response_text,
                "html.parser",
            )

            # ------------------------------------------------
            # Remove unnecessary elements
            # ------------------------------------------------

            for element in soup(
                [
                    "script",
                    "style",
                    "noscript",
                    "svg",
                    "nav",
                    "footer",
                    "header",
                    "form",
                    "aside",
                ]
            ):

                element.decompose()

            # ------------------------------------------------
            # Extract text
            # ------------------------------------------------

            text = soup.get_text(
                separator=" ",
                strip=True,
            )

            if not text:

                return (
                    "No readable text found."
                )

            # ------------------------------------------------
            # IMPORTANT:
            #
            # Previous version returned 18,000 chars.
            # This version returns only 3,000.
            # ------------------------------------------------

            text = text[
                :MAX_WEBPAGE_CHARS
            ]

            return (
                f"Source URL:\n{url}\n\n"
                f"Webpage content:\n{text}\n\n"
                "[Webpage content truncated for "
                "token efficiency.]"
            )

        except requests.RequestException as e:

            return (
                "Could not read webpage: "
                f"{str(e)}"
            )

        except Exception as e:

            return (
                "Could not read webpage: "
                f"{str(e)}"
            )
