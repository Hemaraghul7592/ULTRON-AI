from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from app.operations.validation.domain.models import (
        ValidationCacheEntry,
        ValidationDecision,
        ValidationRequest,
    )


class CacheProvider(Protocol):
    """Abstract provider for validation result caching."""

    async def get(self, request: ValidationRequest) -> ValidationDecision | None:
        """Retrieve a cached validation decision for the request."""
        ...

    async def put(
        self,
        request: ValidationRequest,
        decision: ValidationDecision,
    ) -> None:
        """Store a validation decision in cache."""
        ...

    async def invalidate(self, plan_id: str) -> None:
        """Invalidate cached results for a given plan."""
        ...

    async def get_entry(self, cache_key: str) -> ValidationCacheEntry | None:
        """Retrieve a raw cache entry by key."""
        ...

    async def evict_entry(self, cache_key: str) -> None:
        """Evict a single cache entry by key."""
        ...
