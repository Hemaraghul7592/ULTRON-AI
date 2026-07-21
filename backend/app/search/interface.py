from __future__ import annotations

import abc
from typing import Any, Literal, TypedDict

SearchMode = Literal["standard", "deep"]
SearchDepth = Literal["basic", "advanced"]


class SearchQuery(TypedDict, total=False):
    query: str
    max_results: int
    search_depth: SearchDepth
    include_domains: list[str]
    exclude_domains: list[str]


class SearchResult(TypedDict, total=False):
    title: str
    url: str
    source: str
    snippet: str
    published_date: str | None
    score: float


class SearchResponse(TypedDict, total=False):
    results: list[SearchResult]
    total_results: int
    query: str
    answer: str | None
    provider: str
    cached: bool
    mode: SearchMode


class ResearchQuery(TypedDict, total=False):
    query: str
    max_results: int
    search_depth: SearchDepth


class Citation(TypedDict, total=False):
    title: str
    url: str
    source: str
    snippet: str
    published_date: str | None
    index: int


class ResearchResponse(TypedDict, total=False):
    answer: str
    results: list[SearchResult]
    citations: list[Citation]
    query: str
    provider: str
    cached: bool
    mode: SearchMode
    total_results: int


SearchFeature = Literal["search", "research", "domain_filter", "answer", "deep_research"]


class SearchProvider(abc.ABC):
    @property
    @abc.abstractmethod
    def name(self) -> str:
        pass

    @abc.abstractmethod
    async def search(self, query: SearchQuery) -> SearchResponse:
        pass

    @abc.abstractmethod
    async def research(self, query: ResearchQuery) -> ResearchResponse:
        pass

    async def health_check(self) -> dict[str, Any]:
        return {"status": "available", "provider": self.name}

    async def validate(self) -> bool:
        return True

    def metadata(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "features": self.supported_features(),
        }

    def supported_features(self) -> list[SearchFeature]:
        return ["search", "research"]


class SearchProviderError(Exception):
    def __init__(
        self,
        message: str = "",
        provider: str = "",
        original_error: Exception | None = None,
    ) -> None:
        self.provider = provider
        self.original_error = original_error
        super().__init__(message)


class SearchAuthError(SearchProviderError):
    pass


class SearchRateLimitError(SearchProviderError):
    pass


class SearchTimeoutError(SearchProviderError):
    pass


class SearchUnavailableError(SearchProviderError):
    pass
