from __future__ import annotations

from typing import TYPE_CHECKING

from app.search.interface import SearchFeature, SearchMode, SearchProvider

if TYPE_CHECKING:
    from app.search.service import SearchService

_search_service: SearchService | None = None


def get_search_service() -> SearchService:
    if _search_service is None:
        from app.search.service import SearchService
        raise RuntimeError(
            "SearchService not initialized. Call init_search_service() during app startup."
        )
    return _search_service


def init_search_service(service: SearchService) -> None:
    global _search_service
    _search_service = service


def reset_search_service() -> None:
    global _search_service
    _search_service = None


__all__ = [
    "SearchFeature",
    "SearchMode",
    "SearchProvider",
    "SearchService",
    "get_search_service",
    "init_search_service",
    "reset_search_service",
]

