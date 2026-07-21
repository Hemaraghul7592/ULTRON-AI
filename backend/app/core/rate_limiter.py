from __future__ import annotations

import time
from collections import defaultdict
from threading import Lock
from typing import Any

from app.core.exceptions import RateLimitException
from app.core.logging import get_logger

logger = get_logger(__name__)


class InMemoryRateLimiter:
    def __init__(self, max_requests: int = 60, window_seconds: int = 60) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def _cleanup(self, key: str, now: float) -> None:
        cutoff = now - self.window_seconds
        self._requests[key] = [t for t in self._requests[key] if t > cutoff]

    def check(self, key: str = "global") -> None:
        now = time.monotonic()
        with self._lock:
            self._cleanup(key, now)
            if len(self._requests[key]) >= self.max_requests:
                raise RateLimitException(
                    limit=self.max_requests,
                    window=f"{self.window_seconds}s",
                )
            self._requests[key].append(now)

    def get_remaining(self, key: str = "global") -> int:
        now = time.monotonic()
        with self._lock:
            self._cleanup(key, now)
            return max(0, self.max_requests - len(self._requests[key]))


class RedisRateLimiter:
    def __init__(self, max_requests: int = 60, window_seconds: int = 60) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._redis: Any = None

    async def _get_redis(self) -> Any:
        if self._redis is None:
            from app.core.config import get_settings
            settings = get_settings()
            if not settings.REDIS_URL:
                raise RuntimeError("REDIS_URL not configured")
            import redis.asyncio as aioredis
            self._redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        return self._redis

    async def check(self, key: str = "global") -> None:
        try:
            r = await self._get_redis()
            pipe = r.pipeline()
            now = int(time.time())
            window_start = now - self.window_seconds
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zcard(key)
            pipe.zadd(key, {str(now): now})
            pipe.expire(key, self.window_seconds)
            _, count, _, _ = await pipe.execute()
            if count >= self.max_requests:
                raise RateLimitException(
                    limit=self.max_requests,
                    window=f"{self.window_seconds}s",
                )
        except RateLimitException:
            raise
        except Exception:
            logger.warning("redis_unavailable_falling_back_to_in_memory")
            _in_memory_fallback.check(key=key)

    async def get_remaining(self, key: str = "global") -> int:
        try:
            r = await self._get_redis()
            now = int(time.time())
            window_start = now - self.window_seconds
            await r.zremrangebyscore(key, 0, window_start)
            count = await r.zcard(key)
            return max(0, self.max_requests - count)
        except Exception:
            return _in_memory_fallback.get_remaining(key=key)


_in_memory_fallback = InMemoryRateLimiter()
_redis_limiter: RedisRateLimiter | None = None
_in_memory_limiter: InMemoryRateLimiter | None = None


def get_rate_limiter() -> InMemoryRateLimiter | RedisRateLimiter:
    global _redis_limiter, _in_memory_limiter
    from app.core.config import get_settings

    settings = get_settings()
    if settings.REDIS_URL:
        if _redis_limiter is None:
            _redis_limiter = RedisRateLimiter(max_requests=settings.RATE_LIMIT_PER_MINUTE)
        return _redis_limiter
    if _in_memory_limiter is None:
        _in_memory_limiter = InMemoryRateLimiter(max_requests=settings.RATE_LIMIT_PER_MINUTE)
    return _in_memory_limiter


def get_auth_rate_limiter() -> InMemoryRateLimiter | RedisRateLimiter:
    global _redis_limiter, _in_memory_limiter
    from app.core.config import get_settings

    settings = get_settings()
    if settings.REDIS_URL:
        if _redis_limiter is None:
            _redis_limiter = RedisRateLimiter(max_requests=settings.RATE_LIMIT_AUTH_PER_MINUTE)
        return _redis_limiter
    if _in_memory_limiter is None:
        _in_memory_limiter = InMemoryRateLimiter(max_requests=settings.RATE_LIMIT_AUTH_PER_MINUTE)
    return _in_memory_limiter