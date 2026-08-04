from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: TC002

from app.models.metric import Metric
from app.schemas.observability import MetricCreate  # noqa: TC001


class MetricRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record(self, data: MetricCreate) -> Metric:
        import json

        metric = Metric(
            name=data.name,
            value=data.value,
            unit=data.unit,
            tags_json=json.dumps(data.tags) if data.tags else None,
            source=data.source,
        )
        self.session.add(metric)
        await self.session.flush()
        return metric

    async def get_recent(self, limit: int = 50) -> list[Metric]:
        result = await self.session.execute(
            select(Metric).order_by(Metric.created_at.desc()).limit(limit),
        )
        return list(result.scalars().all())

    async def aggregate(
        self,
        name: str,
        hours: int = 24,
    ) -> dict:
        since = datetime.now(UTC) - timedelta(hours=hours)
        result = await self.session.execute(
            select(
                func.min(Metric.value),
                func.max(Metric.value),
                func.avg(Metric.value),
                func.sum(Metric.value),
                func.count(Metric.id),
            ).where(
                Metric.name == name,
                Metric.created_at >= since,
            ),
        )
        row = result.one()
        return {
            "name": name,
            "min_value": row[0] or 0.0,
            "max_value": row[1] or 0.0,
            "avg_value": row[2] or 0.0,
            "sum_value": row[3] or 0.0,
            "count": row[4] or 0,
        }

    async def get_latency_percentiles(self, hours: int = 24) -> dict[str, float]:
        since = datetime.now(UTC) - timedelta(hours=hours)
        result = await self.session.execute(
            select(Metric.value)
            .where(Metric.name == "request_latency_ms", Metric.created_at >= since)
            .order_by(Metric.value),
        )
        values = [r[0] for r in result.all()]
        if not values:
            return {"p50": 0.0, "p95": 0.0, "p99": 0.0}

        n = len(values)
        return {
            "p50": values[int(n * 0.5)] if n > 0 else 0.0,
            "p95": values[int(n * 0.95)] if n > 0 else 0.0,
            "p99": values[int(n * 0.99)] if n > 0 else 0.0,
        }

    async def cleanup_old(self, days: int = 90) -> int:
        cutoff = datetime.now(UTC) - timedelta(days=days)
        result = await self.session.execute(
            select(Metric).where(Metric.created_at < cutoff),
        )
        metrics = list(result.scalars().all())
        for m in metrics:
            await self.session.delete(m)
        await self.session.flush()
        return len(metrics)
