from __future__ import annotations

import time
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession  # noqa: TC002

from app.core.logging import get_logger
from app.repositories.metric_repo import MetricRepository
from app.repositories.token_repo import TokenRepository
from app.schemas.observability import MetricCreate

logger = get_logger(__name__)


class MetricsService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = MetricRepository(session)
        self.token_repo = TokenRepository(session)
        self._start_time = time.monotonic()

    async def record_request(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        latency_ms: float,
    ) -> None:
        await self.repo.record(
            MetricCreate(
                name="request_latency_ms",
                value=latency_ms,
                unit="ms",
                tags={"endpoint": endpoint, "method": method, "status": status_code},
                source="api",
            ),
        )

    async def record_ai_request(
        self,
        provider: str,
        model: str,
        tokens: int,
        latency_ms: float,
        cost_usd: float = 0.0,
        conversation_id: str | None = None,
    ) -> None:
        await self.repo.record(
            MetricCreate(
                name="ai_request_latency_ms",
                value=latency_ms,
                unit="ms",
                tags={"provider": provider, "model": model},
                source="ai",
            ),
        )
        await self.repo.record(
            MetricCreate(
                name="ai_tokens_used",
                value=tokens,
                unit="tokens",
                tags={"provider": provider, "model": model},
                source="ai",
            ),
        )
        if cost_usd > 0:
            await self.repo.record(
                MetricCreate(
                    name="ai_cost_usd",
                    value=cost_usd,
                    unit="usd",
                    tags={"provider": provider, "model": model},
                    source="ai",
                ),
            )

    async def record_error(
        self,
        error_type: str,
        source: str,
        details: str | None = None,
    ) -> None:
        await self.repo.record(
            MetricCreate(
                name="error_count",
                value=1.0,
                tags={"type": error_type, "details": details or ""},
                source=source,
            ),
        )

    async def record_retry(self, provider: str, attempt: int) -> None:
        await self.repo.record(
            MetricCreate(
                name="retry_count",
                value=1.0,
                tags={"provider": provider, "attempt": str(attempt)},
                source="ai",
            ),
        )

    async def get_latency_percentiles(self, hours: int = 24) -> dict[str, float]:
        return await self.repo.get_latency_percentiles(hours=hours)

    async def get_recent_metrics(self, limit: int = 50) -> list[Any]:
        return await self.repo.get_recent(limit=limit)

    async def get_ai_usage(self, hours: int = 24) -> dict[str, Any]:
        return await self.token_repo.get_by_provider(hours=hours)

    async def get_token_totals(self, hours: int = 24) -> dict[str, Any]:
        return await self.token_repo.get_totals(hours=hours)

    def get_uptime(self) -> float:
        return time.monotonic() - self._start_time
