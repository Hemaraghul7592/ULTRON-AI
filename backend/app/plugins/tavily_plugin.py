from __future__ import annotations

from typing import Any

import httpx

from app.plugins.base import PluginInterface, PluginStatus
from app.tools.base import BaseTool

TAVILY_API_URL = "https://api.tavily.com"


class TavilySearchTool(BaseTool):
    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        self._client: httpx.AsyncClient | None = None

    @property
    def name(self) -> str:
        return "tavily_search"

    @property
    def description(self) -> str:
        return "Search the web using Tavily. Returns relevant results with titles, URLs, and content."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "max_results": {"type": "integer", "default": 5, "description": "Max results (1-10)"},
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
        query = kwargs.get("query", "")
        max_results = kwargs.get("max_results", 5)
        search_depth = kwargs.get("search_depth", "basic")
        include_domains = kwargs.get("include_domains", [])
        exclude_domains = kwargs.get("exclude_domains", [])

        if not self._api_key:
            return "Tavily API key not configured"

        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)

        payload: dict[str, Any] = {
            "api_key": self._api_key,
            "query": query,
            "max_results": min(max_results, 10),
            "search_depth": search_depth,
        }
        if include_domains:
            payload["include_domains"] = include_domains
        if exclude_domains:
            payload["exclude_domains"] = exclude_domains

        for attempt in range(2):
            try:
                resp = await self._client.post(
                    f"{TAVILY_API_URL}/search",
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
                results = data.get("results", [])
                if not results:
                    return f"No results found for '{query}'"
                output = [f"Search results for '{query}' ({len(results)}):"]
                for r in results[:max_results]:
                    title = r.get("title", "")
                    url = r.get("url", "")
                    content = r.get("content", "")
                    score = r.get("score", "")
                    line = f"- {title}" if title else ""
                    line += f" ({url})" if url else ""
                    if content:
                        line += f"\n  {content[:200]}"
                    if score:
                        line += f" [score: {score:.2f}]"
                    output.append(line)
                return "\n".join(output)
            except httpx.HTTPStatusError as e:
                if e.response.status_code >= 500 and attempt == 0:
                    continue
                return f"Tavily search error: {e.response.status_code}"
            except httpx.RequestError as e:
                if attempt == 0:
                    continue
                return f"Tavily search error: {e}"
        return "Tavily search failed after retries"

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()


class TavilyAnswerTool(BaseTool):
    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        self._client: httpx.AsyncClient | None = None

    @property
    def name(self) -> str:
        return "tavily_answer"

    @property
    def description(self) -> str:
        return "Get a concise answer to a question using Tavily. Returns a direct answer with sources."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Question to answer"},
                "max_results": {"type": "integer", "default": 3, "description": "Max sources (1-5)"},
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
        query = kwargs.get("query", "")
        max_results = kwargs.get("max_results", 3)
        search_depth = kwargs.get("search_depth", "advanced")

        if not self._api_key:
            return "Tavily API key not configured"

        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)

        payload: dict[str, Any] = {
            "api_key": self._api_key,
            "query": query,
            "max_results": min(max_results, 5),
            "search_depth": search_depth,
            "include_answer": True,
            "include_raw_content": False,
        }

        for attempt in range(2):
            try:
                resp = await self._client.post(
                    f"{TAVILY_API_URL}/search",
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
                answer = data.get("answer", "")
                results = data.get("results", [])
                output = []
                if answer:
                    output.append(f"Answer: {answer}")
                if results:
                    output.append(f"\nSources ({len(results)}):")
                    for r in results[:max_results]:
                        title = r.get("title", "")
                        url = r.get("url", "")
                        content = r.get("content", "")
                        line = f"- {title}" if title else ""
                        line += f" ({url})" if url else ""
                        if content:
                            line += f"\n  {content[:200]}"
                        output.append(line)
                return "\n".join(output) if output else f"No results for '{query}'"
            except httpx.HTTPStatusError as e:
                if e.response.status_code >= 500 and attempt == 0:
                    continue
                return f"Tavily answer error: {e.response.status_code}"
            except httpx.RequestError as e:
                if attempt == 0:
                    continue
                return f"Tavily answer error: {e}"
        return "Tavily answer failed after retries"

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()


class Plugin(PluginInterface):
    @property
    def name(self) -> str:
        return "tavily"

    @property
    def version(self) -> str:
        return "2.0.0"

    @property
    def description(self) -> str:
        return "Web search and Q&A using Tavily API"

    @property
    def required_credentials(self) -> list[str]:
        return ["TAVILY_API_KEY"]

    def __init__(self) -> None:
        self._tools: list[BaseTool] = []
        self._api_key: str = ""

    def get_tools(self) -> list[BaseTool]:
        return self._tools

    async def initialize(self, config: dict | None = None) -> None:
        from app.core.config import get_settings
        settings = get_settings()
        self._api_key = settings.TAVILY_API_KEY
        if self._api_key:
            self._tools = [
                TavilySearchTool(self._api_key),
                TavilyAnswerTool(self._api_key),
            ]

    async def health_check(self) -> dict:
        import time
        if not self._api_key:
            return {"status": PluginStatus.AUTH_FAILED, "message": "TAVILY_API_KEY not configured", "last_check": time.time()}
        if not self._tools:
            return {"status": PluginStatus.DISABLED, "message": "No tools initialized", "last_check": time.time()}
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{TAVILY_API_URL}/search",
                    json={"api_key": self._api_key, "query": "health", "max_results": 1},
                )
                if resp.status_code == 200:
                    return {"status": PluginStatus.AVAILABLE, "message": "Tavily API reachable", "last_check": time.time()}
                return {"status": PluginStatus.AUTH_FAILED, "message": f"Tavily API returned {resp.status_code}", "last_check": time.time()}
        except Exception as e:
            return {"status": PluginStatus.UNAVAILABLE, "message": str(e), "last_check": time.time()}

    async def validate(self) -> bool:
        return bool(self._api_key)

    async def cleanup(self) -> None:
        for tool in self._tools:
            if hasattr(tool, "close"):
                await tool.close()