from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from app.search.cache import SearchCache
from app.search.interface import (
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
from app.search.providers.tavily import TavilyProvider
from app.search.service import SearchService


class FakeProvider(SearchProvider):
    def __init__(
        self,
        name: str = "fake",
        results: list[dict] | None = None,
        answer: str = "",
        should_fail: bool = False,
        fail_with: type[Exception] | None = None,
    ) -> None:
        self._name = name
        self._results = results or []
        self._answer = answer
        self._should_fail = should_fail
        self._fail_with = fail_with or SearchProviderError

    @property
    def name(self) -> str:
        return self._name

    async def search(self, query: SearchQuery) -> SearchResponse:
        if self._should_fail:
            raise self._fail_with(message="provider error", provider=self._name)
        return SearchResponse(
            results=self._results,
            total_results=len(self._results),
            query=query.get("query", ""),
            answer=None,
            provider=self._name,
            cached=False,
            mode="standard",
        )

    async def research(self, query: SearchQuery) -> ResearchResponse:
        if self._should_fail:
            raise self._fail_with(message="provider error", provider=self._name)
        return ResearchResponse(
            answer=self._answer,
            results=self._results,
            citations=[
                {"title": r.get("title", ""), "url": r.get("url", ""), "source": r.get("source", ""),
                 "snippet": r.get("snippet", ""), "index": i + 1}
                for i, r in enumerate(self._results)
            ],
            query=query.get("query", ""),
            provider=self._name,
            cached=False,
            mode="deep",
            total_results=len(self._results),
        )


@pytest.fixture
def sample_results() -> list[SearchResult]:
    return [
        SearchResult(title="Result 1", url="https://example.com/1", source="example.com", snippet="First result", score=0.95),
        SearchResult(title="Result 2", url="https://example.com/2", source="example.com", snippet="Second result", score=0.85),
    ]


@pytest.fixture
def provider() -> FakeProvider:
    return FakeProvider()


@pytest.fixture
def service(provider: FakeProvider) -> SearchService:
    return SearchService(provider=provider, cache=SearchCache(default_ttl=60), timeout=10.0)


class TestSearchProvider:
    def test_name_property(self) -> None:
        assert FakeProvider(name="test").name == "test"

    @pytest.mark.asyncio
    async def test_health_check_default(self) -> None:
        p = FakeProvider()
        hc = await p.health_check()
        assert hc["status"] == "available"
        assert hc["provider"] == "fake"

    @pytest.mark.asyncio
    async def test_validate_default(self) -> None:
        p = FakeProvider()
        assert await p.validate() is True

    def test_metadata(self) -> None:
        p = FakeProvider(name="test")
        meta = p.metadata()
        assert meta["name"] == "test"
        assert "search" in meta["features"]

    def test_supported_features_default(self) -> None:
        p = FakeProvider()
        features = p.supported_features()
        assert "search" in features
        assert "research" in features


class TestSearchCache:
    @pytest.mark.asyncio
    async def test_cache_miss(self) -> None:
        c = SearchCache()
        result = await c.get(query="test query", mode="standard")
        assert result is None

    @pytest.mark.asyncio
    async def test_cache_hit(self) -> None:
        c = SearchCache(default_ttl=60)
        data = {"results": [{"title": "test"}], "total_results": 1}
        await c.set(query="test query", data=data, mode="standard")
        result = await c.get(query="test query", mode="standard")
        assert result is not None
        assert result["results"][0]["title"] == "test"

    @pytest.mark.asyncio
    async def test_cache_expiry(self) -> None:
        c = SearchCache(default_ttl=0)
        await c.set(query="test", data={"key": "value"}, mode="standard")
        await c.set(query="test", data={"key": "value"}, mode="standard")
        result = await c.get(query="test", mode="standard")
        assert result is None

    @pytest.mark.asyncio
    async def test_cache_different_params_different_keys(self) -> None:
        c = SearchCache(default_ttl=60)
        await c.set(query="hello", data={"a": 1}, mode="standard")
        await c.set(query="world", data={"b": 2}, mode="standard")
        r1 = await c.get(query="hello", mode="standard")
        r2 = await c.get(query="world", mode="standard")
        assert r1["a"] == 1
        assert r2["b"] == 2

    @pytest.mark.asyncio
    async def test_cache_normalizes_query(self) -> None:
        c = SearchCache(default_ttl=60)
        await c.set(query="  Hello World  ", data={"val": 1}, mode="standard")
        result = await c.get(query="hello world", mode="standard")
        assert result is not None and result["val"] == 1

    @pytest.mark.asyncio
    async def test_cache_clear(self) -> None:
        c = SearchCache(default_ttl=60)
        await c.set(query="test", data={"x": 1}, mode="standard")
        await c.clear()
        result = await c.get(query="test", mode="standard")
        assert result is None

    @pytest.mark.asyncio
    async def test_cache_invalidate(self) -> None:
        c = SearchCache(default_ttl=60)
        await c.set(query="test", data={"x": 1}, mode="standard")
        assert await c.invalidate(query="test", mode="standard") is True
        assert await c.invalidate(query="test", mode="standard") is False

    @pytest.mark.asyncio
    async def test_cache_stats(self) -> None:
        c = SearchCache(default_ttl=300)
        stats = await c.stats()
        assert stats["size"] == 0
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["hit_rate"] == 0.0

    @pytest.mark.asyncio
    async def test_cache_tracks_hits_and_misses(self) -> None:
        c = SearchCache(default_ttl=60)
        await c.get(query="a", mode="standard")
        await c.get(query="b", mode="standard")
        await c.set(query="b", data={"val": 1}, mode="standard")
        await c.get(query="b", mode="standard")
        stats = await c.stats()
        assert stats["misses"] == 2
        assert stats["hits"] == 1

    @pytest.mark.asyncio
    async def test_cache_ttl_override(self) -> None:
        c = SearchCache(default_ttl=300)
        await c.set(query="test", data={"x": 1}, ttl=0, mode="standard")
        result = await c.get(query="test", mode="standard")
        assert result is None


class TestSearchService:
    @pytest.mark.asyncio
    async def test_search_success(self, service: SearchService, sample_results: list) -> None:
        service._provider = FakeProvider(results=sample_results)
        response = await service.search(SearchQuery(query="test", max_results=5))
        assert response["total_results"] == 2
        assert response["query"] == "test"
        assert response["cached"] is False
        assert response["provider"] == "fake"

    @pytest.mark.asyncio
    async def test_search_deduplicates(self, service: SearchService) -> None:
        results = [
            SearchResult(title="A", url="https://same.com/a", source="same.com", snippet="dup"),
            SearchResult(title="B", url="https://same.com/a", source="same.com", snippet="dup"),
        ]
        service._provider = FakeProvider(results=results)
        response = await service.search(SearchQuery(query="dedup test"))
        assert response["total_results"] == 1
        assert len(response["results"]) == 1

    @pytest.mark.asyncio
    async def test_search_caches_result(self, service: SearchService, sample_results: list) -> None:
        service._provider = FakeProvider(results=sample_results)
        response1 = await service.search(SearchQuery(query="cached test"))
        assert response1["cached"] is False

        response2 = await service.search(SearchQuery(query="cached test"))
        assert response2["cached"] is True
        assert response2["total_results"] == 2

    @pytest.mark.asyncio
    async def test_search_empty_query(self, service: SearchService) -> None:
        with pytest.raises(ValueError, match="cannot be empty"):
            await service.search(SearchQuery(query=""))

    @pytest.mark.asyncio
    async def test_search_query_too_long(self, service: SearchService) -> None:
        with pytest.raises(ValueError, match="too long"):
            await service.search(SearchQuery(query="x" * 501))

    @pytest.mark.asyncio
    async def test_search_provider_auth_error(self, service: SearchService) -> None:
        service._provider = FakeProvider(should_fail=True, fail_with=SearchAuthError)
        with pytest.raises(SearchAuthError):
            await service.search(SearchQuery(query="test"))

    @pytest.mark.asyncio
    async def test_search_provider_rate_limit(self, service: SearchService) -> None:
        service._provider = FakeProvider(should_fail=True, fail_with=SearchRateLimitError)
        with pytest.raises(SearchRateLimitError):
            await service.search(SearchQuery(query="test"))

    @pytest.mark.asyncio
    async def test_research_success(self, service: SearchService, sample_results: list) -> None:
        service._provider = FakeProvider(results=sample_results, answer="Test answer")
        response = await service.research({"query": "test research", "max_results": 3})
        assert response["answer"] == "Test answer"
        assert len(response["results"]) == 2
        assert len(response["citations"]) == 2
        assert response["cached"] is False
        assert response["mode"] == "deep"

    @pytest.mark.asyncio
    async def test_research_empty_query(self, service: SearchService) -> None:
        with pytest.raises(ValueError, match="cannot be empty"):
            await service.research({"query": ""})

    @pytest.mark.asyncio
    async def test_research_too_long(self, service: SearchService) -> None:
        with pytest.raises(ValueError, match="too long"):
            await service.research({"query": "x" * 501})

    @pytest.mark.asyncio
    async def test_research_caches(self, service: SearchService, sample_results: list) -> None:
        service._provider = FakeProvider(results=sample_results, answer="Answer")
        r1 = await service.research({"query": "cached research"})
        assert r1["cached"] is False
        r2 = await service.research({"query": "cached research"})
        assert r2["cached"] is True

    @pytest.mark.asyncio
    async def test_health_check(self, service: SearchService) -> None:
        health = await service.health_check()
        assert "provider" in health
        assert "cache" in health
        assert "timeout" in health
        assert health["timeout"] == 10.0
        assert health["provider"]["status"] == "available"

    @pytest.mark.asyncio
    async def test_clear_cache(self, service: SearchService, sample_results: list) -> None:
        service._provider = FakeProvider(results=sample_results)
        await service.search(SearchQuery(query="clear test"))
        await service.clear_cache()
        stats = await service.cache_stats()
        assert stats["size"] == 0

    @pytest.mark.asyncio
    async def test_cache_stats(self, service: SearchService) -> None:
        stats = await service.cache_stats()
        assert "size" in stats
        assert "hits" in stats
        assert "misses" in stats

    @pytest.mark.asyncio
    async def test_format_citations(self, service: SearchService, sample_results: list) -> None:
        citations = SearchService.format_citations(sample_results)
        assert len(citations) == 2
        assert citations[0]["index"] == 1
        assert citations[1]["index"] == 2
        assert citations[0]["title"] == "Result 1"
        assert citations[1]["title"] == "Result 2"
        assert citations[0]["source"] == "example.com"

    @pytest.mark.asyncio
    async def test_search_provider_error(self, service: SearchService) -> None:
        service._provider = FakeProvider(should_fail=True, fail_with=SearchProviderError)
        with pytest.raises(SearchProviderError):
            await service.search(SearchQuery(query="test"))


class TestSearchServiceTimeout:
    @pytest.mark.asyncio
    async def test_search_timeout(self) -> None:
        class SlowProvider(FakeProvider):
            async def search(self, query: SearchQuery) -> SearchResponse:
                await asyncio.sleep(10)
                return SearchResponse(results=[], total_results=0, query="", provider="slow")

        svc = SearchService(provider=SlowProvider(), cache=SearchCache(default_ttl=60), timeout=0.01)
        with pytest.raises(SearchProviderError, match="timed out"):
            await svc.search(SearchQuery(query="timeout test"))


class TestEmailAddress:
    pass


class TestSearchIntegration:
    @pytest.mark.asyncio
    async def test_provider_and_service_together(self) -> None:
        provider = FakeProvider(results=[
            SearchResult(title="T1", url="https://a.com", source="a.com", snippet="Snippet 1", score=0.9),
            SearchResult(title="T2", url="https://b.com", source="b.com", snippet="Snippet 2", score=0.8),
        ])
        svc = SearchService(provider=provider, cache=SearchCache(default_ttl=300), timeout=10.0)
        response = await svc.search(SearchQuery(query="integration test"))
        assert response["total_results"] == 2
        assert response["results"][0]["title"] == "T1"
        assert response["results"][1]["url"] == "https://b.com"

        research = await svc.research({"query": "integration research"})
        assert research["mode"] == "deep"
        assert len(research["citations"]) == 2


class TestTavilyProvider:
    @pytest.mark.asyncio
    async def test_name(self) -> None:
        p = TavilyProvider(api_key="test-key")
        assert p.name == "tavily"

    @pytest.mark.asyncio
    async def test_validate_with_key(self) -> None:
        p = TavilyProvider(api_key="test-key")
        assert await p.validate() is True

    @pytest.mark.asyncio
    async def test_validate_without_key(self) -> None:
        p = TavilyProvider(api_key="")
        assert await p.validate() is False

    @pytest.mark.asyncio
    async def test_health_without_key(self) -> None:
        p = TavilyProvider(api_key="")
        hc = await p.health_check()
        assert hc["status"] == "auth_failed"

    @pytest.mark.asyncio
    async def test_search_without_key(self) -> None:
        p = TavilyProvider(api_key="")
        with pytest.raises(SearchAuthError):
            await p.search(SearchQuery(query="test"))

    @pytest.mark.asyncio
    async def test_research_without_key(self) -> None:
        p = TavilyProvider(api_key="")
        with pytest.raises(SearchAuthError):
            await p.research({"query": "test"})

    @pytest.mark.asyncio
    async def test_supported_features(self) -> None:
        p = TavilyProvider(api_key="test")
        features = p.supported_features()
        assert "search" in features
        assert "research" in features
        assert "domain_filter" in features
        assert "answer" in features

    def test_metadata(self) -> None:
        p = TavilyProvider(api_key="test")
        meta = p.metadata()
        assert meta["name"] == "tavily"

    def test_extract_source(self) -> None:
        source = TavilyProvider._extract_source("https://www.example.com/page")
        assert source == "example.com"

    def test_extract_source_empty(self) -> None:
        assert TavilyProvider._extract_source("") == ""

    def test_extract_source_no_www(self) -> None:
        source = TavilyProvider._extract_source("https://blog.example.com")
        assert source == "blog.example.com"

    @pytest.mark.asyncio
    async def test_close(self) -> None:
        p = TavilyProvider(api_key="test")
        await p.close()


class TestSearchServiceCacheIntegration:
    @pytest.mark.asyncio
    async def test_cache_works_across_search_and_research(self) -> None:
        provider = FakeProvider(results=[
            SearchResult(title="R1", url="https://x.com", source="x.com", snippet="X", score=0.9),
        ], answer="Answer text")
        svc = SearchService(provider=provider, cache=SearchCache(default_ttl=60), timeout=10.0)

        r1 = await svc.search(SearchQuery(query="hello"))
        assert r1["cached"] is False
        r2 = await svc.search(SearchQuery(query="hello"))
        assert r2["cached"] is True

        rr1 = await svc.research({"query": "world"})
        assert rr1["cached"] is False
        rr2 = await svc.research({"query": "world"})
        assert rr2["cached"] is True

    @pytest.mark.asyncio
    async def test_cache_key_differs_by_mode(self) -> None:
        provider = FakeProvider(results=[SearchResult(title="R", url="https://x.com", source="x.com", snippet="X", score=0.9)])
        svc = SearchService(provider=provider, cache=SearchCache(default_ttl=60), timeout=10.0)

        await svc.search(SearchQuery(query="same query"))
        r = await svc.research({"query": "same query"})
        assert r["cached"] is False

    @pytest.mark.asyncio
    async def test_deduplication_across_research_citations(self) -> None:
        results = [
            SearchResult(title="A", url="https://dup.com", source="dup.com", snippet="Dup", score=0.9),
            SearchResult(title="A", url="https://dup.com", source="dup.com", snippet="Dup", score=0.9),
        ]
        provider = FakeProvider(results=results, answer="Answer")
        svc = SearchService(provider=provider, cache=SearchCache(default_ttl=60), timeout=10.0)

        response = await svc.research({"query": "dup test"})
        assert len(response["results"]) == 1
