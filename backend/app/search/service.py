from __future__ import annotations

import asyncio
from typing import Any

from app.core.logging import get_logger
from app.search.cache import SearchCache
from app.search.interface import (
    ResearchQuery,
    ResearchResponse,
    SearchProvider,
    SearchProviderError,
    SearchQuery,
    SearchResponse,
    SearchResult,
)

logger = get_logger(__name__)

DEFAULT_TIMEOUT = 25.0
DEFAULT_MAX_RETRIES = 2


class SearchService:
    def __init__(
        self,
        provider: SearchProvider,
        cache: SearchCache | None = None,
        default_ttl: int = 300,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self._provider = provider
        self._cache = cache or SearchCache(default_ttl=default_ttl)
        self._timeout = timeout

    @property
    def provider(self) -> SearchProvider:
        return self._provider

    @property
    def cache(self) -> SearchCache:
        return self._cache

    def _cache_params(self, query: SearchQuery | ResearchQuery, mode: str) -> dict[str, Any]:
        params: dict[str, Any] = {"mode": mode}
        if "search_depth" in query:
            params["search_depth"] = query["search_depth"]
        if "max_results" in query:
            params["max_results"] = query["max_results"]
        if "include_domains" in query:
            params["include_domains"] = str(query["include_domains"])
        if "exclude_domains" in query:
            params["exclude_domains"] = str(query["exclude_domains"])
        return params

    async def search(self, query: SearchQuery) -> SearchResponse:
        q = query.get("query", "").strip()
        if not q:
            raise ValueError("Search query cannot be empty")

        if len(q) > 500:
            raise ValueError("Search query too long (max 500 characters)")

        cache_params = self._cache_params(query, "standard")
        try:
            cached = await self._cache.get(query=q, **cache_params)
            if cached is not None:
                cached["cached"] = True
                return cached

            result = await asyncio.wait_for(
                self._provider.search(query),
                timeout=self._timeout,
            )

            result["cached"] = False
            result = self._deduplicate(result)

            await self._cache.set(query=q, data=result, **cache_params)
            return result

        except TimeoutError as e:
            logger.error("search_timeout", query=q[:50])
            raise SearchProviderError(
                message=f"Search timed out after {self._timeout}s",
                provider=self._provider.name,
            ) from e

    async def research(self, query: ResearchQuery) -> ResearchResponse:
        q = query.get("query", "").strip()
        if not q:
            raise ValueError("Research query cannot be empty")

        if len(q) > 500:
            raise ValueError("Research query too long (max 500 characters)")

        cache_params = self._cache_params(query, "deep")
        try:
            cached = await self._cache.get(query=q, **cache_params)
            if cached is not None:
                cached["cached"] = True
                return cached

            result = await asyncio.wait_for(
                self._provider.research(query),
                timeout=self._timeout,
            )

            result["cached"] = False
            result["results"] = self._deduplicate_results(result.get("results", []))
            if "citations" in result:
                result["citations"] = self._deduplicate_results(result["citations"])

            await self._cache.set(query=q, data=result, **cache_params)
            return result

        except TimeoutError as e_re:
            logger.error("research_timeout", query=q[:50])
            raise SearchProviderError(
                message=f"Research timed out after {self._timeout}s",
                provider=self._provider.name,
            ) from e_re

    async def health_check(self) -> dict[str, Any]:
        provider_health = await self._provider.health_check()
        cache_stats = await self._cache.stats()
        return {
            "provider": provider_health,
            "cache": cache_stats,
            "timeout": self._timeout,
        }

    async def clear_cache(self) -> None:
        await self._cache.clear()

    async def cache_stats(self) -> dict[str, Any]:
        return await self._cache.stats()

    def _deduplicate(self, response: SearchResponse) -> SearchResponse:
        response["results"] = self._deduplicate_results(response.get("results", []))
        response["total_results"] = len(response["results"])
        return response

    @staticmethod
    def _deduplicate_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen_urls: set[str] = set()
        deduped: list[dict[str, Any]] = []
        for r in results:
            url = r.get("url", "")
            if url and url in seen_urls:
                continue
            if url:
                seen_urls.add(url)
            deduped.append(r)
        return deduped

    @staticmethod
    def format_citations(results: list[SearchResult]) -> list[dict[str, Any]]:
        return [
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "source": r.get("source", ""),
                "snippet": r.get("snippet", ""),
                "published_date": r.get("published_date"),
                "index": i + 1,
            }
            for i, r in enumerate(results)
        ]
