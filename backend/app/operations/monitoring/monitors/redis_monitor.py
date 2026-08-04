from __future__ import annotations

import time as time_module
from typing import TYPE_CHECKING

from app.core.config import get_settings
from app.operations.domain.enums import ComponentType
from app.operations.monitoring.monitors.base import (
    BaseMonitor,
    _healthy,
    _not_configured,
    _offline,
)

if TYPE_CHECKING:
    from app.operations.domain.models import ComponentHealth


class RedisMonitor(BaseMonitor):
    component_type = ComponentType.REDIS
    component_name = "redis-cache"

    async def _do_check(self) -> ComponentHealth:
        settings = get_settings()
        if not settings.REDIS_URL:
            return _not_configured(
                self.component_type,
                self.component_name,
                self.environment,
                message="Redis URL not configured",
            )

        try:
            import redis.asyncio as aioredis

            start = time_module.time()
            r = aioredis.from_url(
                settings.REDIS_URL, decode_responses=True, socket_connect_timeout=2
            )
            await r.ping()
            latency_ms = round((time_module.time() - start) * 1000, 2)
            await r.aclose()
            return _healthy(
                self.component_type,
                self.component_name,
                self.environment,
                message="Redis is responsive",
                details={"latency_ms": str(latency_ms), "url": settings.REDIS_URL},
            )
        except Exception as exc:  # noqa: BLE001
            return _offline(
                self.component_type,
                self.component_name,
                self.environment,
                message=f"Redis check failed: {exc}",
                details={"error": str(exc)},
            )
