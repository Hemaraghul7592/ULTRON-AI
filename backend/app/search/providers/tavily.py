from __future__ import annotations

from typing import Any

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger
from app.search.interface import (
    ResearchQuery,
    ResearchResponse,
    SearchAuthError,
    SearchProvider,
    SearchProviderError,
    SearchQuery,
    SearchRateLimitError,
    SearchResponse,
    SearchResult,
    SearchTimeoutError,
    SearchUnavailableError,
)

logger = get_logger(__name__)

TAVILY_API_URL = "https://api.tavily.com"


class TavilyProvider(SearchProvider):
    def __init__(self, api_key: str | None = None) -> None:
        if api_key is None:
            settings = get_settings()
            self._api_key = settings.TAVILY_API_KEY
        else:
            self._api_key = api_key
        self._client: httpx.AsyncClient | None = None

    @property
    def name(self) -> str:
        return "tavily"

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def search(self, query: SearchQuery) -> SearchResponse:
        q = query.get("query", "")
        max_results = query.get("max_results", 5)
        search_depth = query.get("search_depth", "basic")
        include_domains = query.get("include_domains", [])
        exclude_domains = query.get("exclude_domains", [])

        if not self._api_key:
            raise SearchAuthError(message="TAVILY_API_KEY not configured", provider="tavily")

        payload: dict[str, Any] = {
            "api_key": self._api_key,
            "query": q,
            "max_results": min(max_results, 10),
            "search_depth": search_depth,
        }
        if include_domains:
            payload["include_domains"] = include_domains
        if exclude_domains:
            payload["exclude_domains"] = exclude_domains

        data = await self._call_api(payload)

        raw_results = data.get("results", [])
        results = [
            SearchResult(
                title=r.get("title", ""),
                url=r.get("url", ""),
                source=self._extract_source(r.get("url", "")),
                snippet=r.get("content", ""),
                published_date=None,
                score=r.get("score", 0.0),
            )
            for r in raw_results
        ]

        return SearchResponse(
            results=results,
            total_results=len(results),
            query=q,
            answer=None,
            provider="tavily",
            cached=False,
            mode="standard",
        )

    async def research(self, query: ResearchQuery) -> ResearchResponse:
        q = query.get("query", "")
        max_results = query.get("max_results", 3)
        search_depth = query.get("search_depth", "advanced")

        if not self._api_key:
            raise SearchAuthError(message="TAVILY_API_KEY not configured", provider="tavily")

        payload: dict[str, Any] = {
            "api_key": self._api_key,
            "query": q,
            "max_results": min(max_results, 5),
            "search_depth": search_depth,
            "include_answer": True,
            "include_raw_content": False,
        }

        data = await self._call_api(payload)

        answer = data.get("answer", "")
        raw_results = data.get("results", [])

        results = [
            SearchResult(
                title=r.get("title", ""),
                url=r.get("url", ""),
                source=self._extract_source(r.get("url", "")),
                snippet=r.get("content", ""),
                published_date=None,
                score=r.get("score", 0.0),
            )
            for r in raw_results[:max_results]
        ]

        citations = [
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "source": self._extract_source(r.get("url", "")),
                "snippet": r.get("content", ""),
                "published_date": None,
                "index": i + 1,
            }
            for i, r in enumerate(raw_results[:max_results])
        ]

        return ResearchResponse(
            answer=answer,
            results=results,
            citations=citations,
            query=q,
            provider="tavily",
            cached=False,
            mode="deep",
            total_results=len(results),
        )

    async def _call_api(self, payload: dict[str, Any]) -> dict[str, Any]:
        client = self._get_client()
        for attempt in range(2):
            try:
                resp = await client.post(f"{TAVILY_API_URL}/search", json=payload)
                if resp.status_code == 200:
                    return resp.json()

                if resp.status_code == 401 or resp.status_code == 403:
                    raise SearchAuthError(
                        message=f"Tavily auth error: {resp.status_code}",
                        provider="tavily",
                    )
                if resp.status_code == 429:
                    raise SearchRateLimitError(
                        message="Tavily rate limited",
                        provider="tavily",
                    )
                if resp.status_code >= 500 and attempt == 0:
                    continue
                raise SearchProviderError(
                    message=f"Tavily error: {resp.status_code}",
                    provider="tavily",
                )

            except httpx.TimeoutException as e:
                if attempt == 0:
                    continue
                raise SearchTimeoutError(
                    message="Tavily request timed out",
                    provider="tavily",
                ) from e
            except httpx.RequestError as e:
                if attempt == 0:
                    continue
                raise SearchUnavailableError(
                    message="Tavily unavailable (network error)",
                    provider="tavily",
                ) from e

        raise SearchProviderError(
            message="Tavily failed after retries",
            provider="tavily",
        )

    async def health_check(self) -> dict[str, Any]:
        if not self._api_key:
            return {
                "status": "auth_failed",
                "provider": "tavily",
                "message": "TAVILY_API_KEY not configured",
            }
        try:
            client = self._get_client()
            resp = await client.post(
                f"{TAVILY_API_URL}/search",
                json={"api_key": self._api_key, "query": "health", "max_results": 1},
            )
            if resp.status_code == 200:
                return {"status": "available", "provider": "tavily", "message": "API reachable"}
            return {
                "status": "auth_failed",
                "provider": "tavily",
                "message": f"API returned {resp.status_code}",
            }
        except Exception as e:
            return {"status": "unavailable", "provider": "tavily", "message": str(e)}

    async def validate(self) -> bool:
        return bool(self._api_key)

    def metadata(self) -> dict[str, Any]:
        return {
            "name": "tavily",
            "features": self.supported_features(),
        }

    def supported_features(self) -> list[str]:
        return ["search", "research", "domain_filter", "answer"]

    @staticmethod
    def _extract_source(url: str) -> str:
        if not url:
            return ""
        try:
            from urllib.parse import urlparse

            parsed = urlparse(url)
            hostname = parsed.hostname or ""
            return hostname.replace("www.", "")
        except Exception:
            return url
