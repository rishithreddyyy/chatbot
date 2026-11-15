"""
Google Search / Web Search Agent tools for Code Forge AI.
Provides real-time web querying, documentation lookup, dedicated coding search,
and webpage content extraction with auto-summarization.
"""

from typing import List, Dict, Any, Optional
import urllib.parse
import re
import requests
from bs4 import BeautifulSoup
from tools.base import BaseTool, ToolResult

try:
    from ddgs import DDGS
    DDG_AVAILABLE = True
except ImportError:
    try:
        from duckduckgo_search import DDGS
        DDG_AVAILABLE = True
    except ImportError:
        DDG_AVAILABLE = False


class WebSearchTool(BaseTool):
    """Searches the live web for technical documentation, errors, news, and current information."""
    name = "web_search"
    description = (
        "Search Google / the web for technical documentation, bug fixes, API specs, "
        "news, or general factual information. Returns relevant titles, snippets, and URLs."
    )
    agent_name = "Google Search Agent"
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query (e.g. 'fastapi async routes example' or 'latest tech news')"
            },
            "num_results": {
                "type": "integer",
                "description": "Number of search results to return (default 5, max 10)",
                "default": 5
            }
        },
        "required": ["query"]
    }

    def execute(self, query: str, num_results: int = 5, **kwargs) -> ToolResult:
        num_results = min(max(1, int(num_results)), 10)
        results = []

        # 1. Try DuckDuckGo / DDGS Search API
        if DDG_AVAILABLE:
            try:
                with DDGS() as ddgs:
                    ddg_results = list(ddgs.text(query, max_results=num_results))
                    for r in ddg_results:
                        results.append({
                            "title": r.get("title", "No Title"),
                            "snippet": r.get("body", ""),
                            "url": r.get("href", "")
                        })
            except Exception:
                pass

        # 2. Fallback to direct HTML search if no results or exception
        if not results:
            try:
                headers = {
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    )
                }
                encoded_query = urllib.parse.quote_plus(query)
                url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
                resp = requests.get(url, headers=headers, timeout=10)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    links = soup.find_all("a", class_="result__snippet", limit=num_results)
                    titles = soup.find_all("a", class_="result__url", limit=num_results)
                    for i, (l, t) in enumerate(zip(links, titles)):
                        results.append({
                            "title": t.get_text(strip=True),
                            "snippet": l.get_text(strip=True),
                            "url": t.get("href", "")
                        })
            except Exception:
                pass

        if not results:
            return ToolResult(
                success=False,
                output=f"No results found for search query: '{query}'. Please try rephrasing.",
                error="Empty search result or connection issue",
                agent_name=self.agent_name
            )

        # Format output
        output_lines = [f"Search Results for: '{query}'\n"]
        for idx, res in enumerate(results, 1):
            output_lines.append(f"{idx}. {res['title']}")
            output_lines.append(f"   URL: {res['url']}")
            output_lines.append(f"   Snippet: {res['snippet']}\n")

        formatted_output = "\n".join(output_lines)
        return ToolResult(
            success=True,
            output=formatted_output,
            data={"results": results, "query": query},
            agent_name=self.agent_name
        )


class CodingSearchTool(BaseTool):
    """Targeted search specifically for programming errors, StackOverflow solutions, and library docs."""
    name = "coding_search"
    description = "Searches specifically for programming errors, GitHub issues, StackOverflow discussions, and official code documentation."
    agent_name = "Google Search Agent"
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Error message, function, or programming concept to search"
            },
            "language": {
                "type": "string",
                "description": "Programming language (e.g. 'python', 'javascript', 'sql', 'java', 'c++')",
                "default": ""
            }
        },
        "required": ["query"]
    }

    def execute(self, query: str, language: str = "", **kwargs) -> ToolResult:
        targeted_query = f"{language} {query} stackoverflow github documentation".strip()
        searcher = WebSearchTool()
        res = searcher.execute(query=targeted_query, num_results=5)
        res.agent_name = self.agent_name
        return res


class FetchWebpageTool(BaseTool):
    """Fetches the readable text content of a webpage (e.g. documentation or article)."""
    name = "fetch_webpage"
    description = (
        "Fetches and extracts readable text from a specific URL. "
        "Useful for reading library documentation, GitHub files, or StackOverflow answers."
    )
    agent_name = "Google Search Agent"
    parameters = {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The full URL of the webpage to fetch"
            },
            "max_chars": {
                "type": "integer",
                "description": "Maximum characters of text to return (default: 4000)",
                "default": 4000
            }
        },
        "required": ["url"]
    }

    def execute(self, url: str, max_chars: int = 4000, **kwargs) -> ToolResult:
        try:
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
            }
            resp = requests.get(url, headers=headers, timeout=12)
            if resp.status_code != 200:
                return ToolResult(
                    success=False,
                    output=f"Failed to fetch {url}. HTTP Status Code: {resp.status_code}",
                    error=f"HTTP {resp.status_code}",
                    agent_name=self.agent_name
                )

            soup = BeautifulSoup(resp.text, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
                tag.decompose()

            text = soup.get_text(separator="\n", strip=True)
            text = re.sub(r"\n\s*\n+", "\n\n", text)

            if len(text) > max_chars:
                text = text[:max_chars] + f"\n\n... [Content truncated at {max_chars} characters]"

            return ToolResult(
                success=True,
                output=f"Content from {url}:\n\n{text}",
                data={"url": url, "text": text},
                agent_name=self.agent_name
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output=f"Error fetching URL {url}: {str(e)}",
                error=str(e),
                agent_name=self.agent_name
            )


class SearchDocumentationTool(BaseTool):
    """Targeted search for official programming documentation."""
    name = "search_documentation"
    description = (
        "Performs a specialized documentation search for libraries like Python, Pandas, "
        "Streamlit, PyTorch, React, FastAPI, etc."
    )
    agent_name = "Google Search Agent"
    parameters = {
        "type": "object",
        "properties": {
            "library": {
                "type": "string",
                "description": "Library or language name (e.g., 'streamlit', 'pandas', 'fastapi', 'yfinance')"
            },
            "query": {
                "type": "string",
                "description": "What you want to look up (e.g., 'st.dataframe column configuration' or 'groupby rolling mean')"
            }
        },
        "required": ["library", "query"]
    }

    def execute(self, library: str, query: str, **kwargs) -> ToolResult:
        targeted_query = f"{library} documentation official {query}"
        searcher = WebSearchTool()
        res = searcher.execute(query=targeted_query, num_results=5)
        res.agent_name = self.agent_name
        return res


def summarize_search_results(results: List[Dict[str, str]], query: str) -> str:
    """Summarizes search results in clean, simple English with bullet points."""
    if not results:
        return f"No results to summarize for '{query}'."

    summary_points = []
    for r in results[:4]:
        snippet = r.get("snippet", "").strip()
        if snippet:
            # Clean snippet of weird characters
            clean_s = re.sub(r"\s+", " ", snippet)
            summary_points.append(f"• **{r.get('title', 'Info')}**: {clean_s}")

    return "\n".join(summary_points)


class SearchAgent:
    """High-level autonomous search agent interface."""
    def __init__(self):
        self.web_search = WebSearchTool()
        self.coding_search = CodingSearchTool()
        self.fetch_webpage = FetchWebpageTool()
        self.search_doc = SearchDocumentationTool()

    def get_tools(self) -> List[BaseTool]:
        return [self.web_search, self.coding_search, self.fetch_webpage, self.search_doc]

    def query(self, prompt: str) -> str:
        res = self.web_search.execute(query=prompt, num_results=5)
        return res.output
