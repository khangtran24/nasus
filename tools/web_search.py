"""Web search tools."""

from __future__ import annotations

from typing import Any, Dict, List

try:
    from duckduckgo_search import DDGS
    HAS_DDGS = True
except ImportError:
    HAS_DDGS = False


class WebSearch:
    """Web search using DuckDuckGo."""

    def __init__(self, max_results: int = 5):
        """Initialize web search.

        Args:
            max_results: Maximum number of results to return
        """
        self.max_results = max_results

        if not HAS_DDGS:
            raise ImportError(
                "duckduckgo-search not installed. "
                "Install with: pip install duckduckgo-search"
            )

    def search(self, query: str, max_results: int | None = None) -> List[Dict[str, Any]]:
        """Search the web using DuckDuckGo.

        Args:
            query: Search query
            max_results: Maximum results (uses default if not provided)

        Returns:
            List of search results with title, url, and snippet
        """
        max_results = max_results or self.max_results

        try:
            with DDGS() as ddgs:
                results = []
                for result in ddgs.text(query, max_results=max_results):
                    results.append({
                        "title": result.get("title", ""),
                        "url": result.get("href", ""),
                        "snippet": result.get("body", ""),
                    })

                return results

        except Exception as e:
            return [{
                "error": f"Search failed: {str(e)}",
                "query": query
            }]

    def search_documentation(
        self,
        package: str,
        topic: str | None = None
    ) -> List[Dict[str, Any]]:
        """Search for package documentation.

        Args:
            package: Package name (e.g., "anthropic")
            topic: Optional specific topic

        Returns:
            List of documentation results
        """
        if topic:
            query = f"{package} documentation {topic}"
        else:
            query = f"{package} documentation"

        return self.search(query)

    def search_stackoverflow(
        self,
        query: str,
        max_results: int | None = None
    ) -> List[Dict[str, Any]]:
        """Search Stack Overflow.

        Args:
            query: Search query
            max_results: Maximum results

        Returns:
            List of Stack Overflow results
        """
        so_query = f"site:stackoverflow.com {query}"
        return self.search(so_query, max_results)

    def search_github(
        self,
        query: str,
        max_results: int | None = None
    ) -> List[Dict[str, Any]]:
        """Search GitHub.

        Args:
            query: Search query
            max_results: Maximum results

        Returns:
            List of GitHub results
        """
        gh_query = f"site:github.com {query}"
        return self.search(gh_query, max_results)
