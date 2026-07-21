from __future__ import annotations

from typing import Any

from app.plugins.base import PluginInterface, PluginStatus
from app.search import get_search_service
from app.search.interface import ResearchQuery, SearchQuery
from app.tools.base import BaseTool


class TavilySearchTool(BaseTool):
    @property
    def name(self) -> str:
        return "tavily_search"

    @property
    def description(self) -> str:
        return (
            "Search the web using Tavily. Returns relevant results with titles, URLs, and content."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "max_results": {
                    "type": "integer",
                    "default": 5,
                    "description": "Max results (1-10)",
                },
                "search_depth": {
                    "type": "string",
                    "enum": ["basic", "advanced"],
                    "default": "basic",
                    "description": "Search depth",
                },
                "include_domains": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Limit to specific domains",
                },
                "exclude_domains": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Exclude specific domains",
                },
            },
            "required": ["query"],
        }

    async def execute(self, **kwargs: Any) -> str:
        query = SearchQuery(
            query=kwargs.get("query", ""),
            max_results=kwargs.get("max_results", 5),
            search_depth=kwargs.get("search_depth", "basic"),
            include_domains=kwargs.get("include_domains", []),
            exclude_domains=kwargs.get("exclude_domains", []),
        )

        try:
            service = get_search_service()
            response = await service.search(query)
            results = response.get("results", [])
            if not results:
                return f"No results found for '{query['query']}'"
            output = [f"Search results for '{query['query']}' ({len(results)}):"]
            for r in results:
                title = r.get("title", "")
                url = r.get("url", "")
                snippet = r.get("snippet", "")
                score = r.get("score", 0.0)
                line = f"- {title}" if title else ""
                line += f" ({url})" if url else ""
                if snippet:
                    line += f"\n  {snippet[:200]}"
                if score:
                    line += f" [score: {score:.2f}]"
                output.append(line)
            cached = response.get("cached", False)
            if cached:
                output.append("\n(Results from cache)")
            return "\n".join(output)
        except Exception as e:
            return f"Tavily search error: {e}"


class TavilyAnswerTool(BaseTool):
    @property
    def name(self) -> str:
        return "tavily_answer"

    @property
    def description(self) -> str:
        return (
            "Get a concise answer to a question using Tavily. Returns a direct answer with sources."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Question to answer"},
                "max_results": {
                    "type": "integer",
                    "default": 3,
                    "description": "Max sources (1-5)",
                },
                "search_depth": {
                    "type": "string",
                    "enum": ["basic", "advanced"],
                    "default": "advanced",
                    "description": "Search depth for answer quality",
                },
            },
            "required": ["query"],
        }

    async def execute(self, **kwargs: Any) -> str:
        query = ResearchQuery(
            query=kwargs.get("query", ""),
            max_results=kwargs.get("max_results", 3),
            search_depth=kwargs.get("search_depth", "advanced"),
        )

        try:
            service = get_search_service()
            response = await service.research(query)
            answer = response.get("answer", "")
            results = response.get("results", [])
            citations = response.get("citations", [])

            if not answer and not results:
                return f"No results for '{query['query']}'"

            output = []
            if answer:
                output.append(f"Answer: {answer}")
            if citations:
                output.append(f"\nSources ({len(citations)}):")
                for c in citations:
                    title = c.get("title", "")
                    url = c.get("url", "")
                    snippet = c.get("snippet", "")
                    idx = c.get("index", "")
                    line = f"[{idx}] {title}" if title else ""
                    line += f" ({url})" if url else ""
                    if snippet:
                        line += f"\n    {snippet[:200]}"
                    output.append(line)
            elif results:
                output.append(f"\nSources ({len(results)}):")
                for r in results:
                    title = r.get("title", "")
                    url = r.get("url", "")
                    snippet = r.get("snippet", "")
                    line = f"- {title}" if title else ""
                    line += f" ({url})" if url else ""
                    if snippet:
                        line += f"\n  {snippet[:200]}"
                    output.append(line)
            cached = response.get("cached", False)
            if cached:
                output.append("\n(Results from cache)")
            return "\n".join(output)
        except Exception as e:
            return f"Tavily answer error: {e}"


class Plugin(PluginInterface):
    @property
    def name(self) -> str:
        return "tavily"

    @property
    def version(self) -> str:
        return "3.0.0"

    @property
    def description(self) -> str:
        return "Web search and Q&A using Tavily API (via SearchService)"

    @property
    def required_credentials(self) -> list[str]:
        return ["TAVILY_API_KEY"]

    def __init__(self) -> None:
        self._tools: list[BaseTool] = []

    def get_tools(self) -> list[BaseTool]:
        return self._tools

    async def initialize(self, config: dict | None = None) -> None:
        from app.core.config import get_settings

        settings = get_settings()
        if settings.TAVILY_API_KEY:
            self._tools = [
                TavilySearchTool(),
                TavilyAnswerTool(),
            ]

    async def health_check(self) -> dict:
        import time

        from app.core.config import get_settings

        settings = get_settings()
        if not settings.TAVILY_API_KEY:
            return {
                "status": PluginStatus.AUTH_FAILED,
                "message": "TAVILY_API_KEY not configured",
                "last_check": time.time(),
            }
        if not self._tools:
            return {
                "status": PluginStatus.DISABLED,
                "message": "No tools initialized",
                "last_check": time.time(),
            }
        try:
            service = get_search_service()
            health = await service.health_check()
            provider_health = health.get("provider", {})
            status = provider_health.get("status", PluginStatus.UNAVAILABLE)
            return {
                "status": status,
                "message": provider_health.get("message", ""),
                "last_check": time.time(),
            }
        except Exception as e:
            return {
                "status": PluginStatus.UNAVAILABLE,
                "message": str(e),
                "last_check": time.time(),
            }

    async def validate(self) -> bool:
        from app.core.config import get_settings

        return bool(get_settings().TAVILY_API_KEY)

    async def cleanup(self) -> None:
        pass
