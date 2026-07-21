from __future__ import annotations

import hashlib
import json
import time
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


class CacheEntry:
    def __init__(self, data: Any, ttl: float) -> None:
        self.data = data
        self.expires_at = time.time() + ttl

    def is_expired(self) -> bool:
        return time.time() > self.expires_at

    def ttl_remaining(self) -> float:
        return max(0.0, self.expires_at - time.time())


class SearchCache:
    def __init__(self, default_ttl: int = 300) -> None:
        self._cache: dict[str, CacheEntry] = {}
        self._default_ttl = default_ttl
        self._hits = 0
        self._misses = 0

    def _make_key(self, query: str, **params: Any) -> str:
        normalized = query.strip().lower()
        raw = json.dumps({"query": normalized, **params}, sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()

    async def get(self, query: str, **params: Any) -> Any | None:
        key = self._make_key(query, **params)
        entry = self._cache.get(key)
        if entry is None:
            self._misses += 1
            return None
        if entry.is_expired():
            self._cache.pop(key, None)
            self._misses += 1
            return None
        self._hits += 1
        logger.debug("cache_hit", key=key[:8])
        return entry.data

    async def set(
        self,
        query: str,
        data: Any,
        ttl: int | None = None,
        **params: Any,
    ) -> None:
        key = self._make_key(query, **params)
        effective_ttl = ttl if ttl is not None else self._default_ttl
        self._cache[key] = CacheEntry(data, float(effective_ttl))
        logger.debug("cache_set", key=key[:8], ttl=effective_ttl)

    async def clear(self) -> None:
        self._cache.clear()
        self._hits = 0
        self._misses = 0
        logger.info("cache_cleared")

    async def invalidate(self, query: str, **params: Any) -> bool:
        key = self._make_key(query, **params)
        existed = key in self._cache
        self._cache.pop(key, None)
        return existed

    async def stats(self) -> dict[str, Any]:
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0.0
        return {
            "size": len(self._cache),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(hit_rate, 4),
            "default_ttl": self._default_ttl,
        }

    @property
    def size(self) -> int:
        return len(self._cache)
