from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: TC002

from app.models.token import TokenUsage


class TokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record(
        self,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        cost_usd: float = 0.0,
        request_id: str | None = None,
        conversation_id: str | None = None,
        user_id: str | None = None,
    ) -> TokenUsage:
        usage = TokenUsage(
            provider=provider,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            cost_usd=cost_usd,
            request_id=request_id,
            conversation_id=conversation_id,
            user_id=user_id,
        )
        self.session.add(usage)
        await self.session.flush()
        return usage

    async def get_totals(self, hours: int = 24) -> dict:
        since = datetime.now(UTC) - timedelta(hours=hours)
        result = await self.session.execute(
            select(
                func.sum(TokenUsage.total_tokens),
                func.sum(TokenUsage.cost_usd),
                func.count(TokenUsage.id),
            ).where(TokenUsage.created_at >= since),
        )
        row = result.one()
        return {
            "total_tokens": row[0] or 0,
            "total_cost_usd": row[1] or 0.0,
            "total_requests": row[2] or 0,
        }

    async def get_by_provider(self, hours: int = 24) -> dict[str, dict]:
        since = datetime.now(UTC) - timedelta(hours=hours)
        result = await self.session.execute(
            select(
                TokenUsage.provider,
                func.sum(TokenUsage.total_tokens),
                func.sum(TokenUsage.cost_usd),
                func.count(TokenUsage.id),
            )
            .where(TokenUsage.created_at >= since)
            .group_by(TokenUsage.provider),
        )
        providers = {}
        for row in result.all():
            providers[row[0]] = {
                "total_tokens": row[1] or 0,
                "total_cost_usd": row[2] or 0.0,
                "total_requests": row[3] or 0,
            }
        return providers

    async def get_by_model(self, hours: int = 24) -> dict[str, dict]:
        since = datetime.now(UTC) - timedelta(hours=hours)
        result = await self.session.execute(
            select(
                TokenUsage.model,
                func.sum(TokenUsage.total_tokens),
                func.count(TokenUsage.id),
            )
            .where(TokenUsage.created_at >= since)
            .group_by(TokenUsage.model),
        )
        models = {}
        for row in result.all():
            models[row[0]] = {
                "total_tokens": row[1] or 0,
                "total_requests": row[2] or 0,
            }
        return models

    async def get_hourly_usage(self, hours: int = 24) -> list[dict]:
        since = datetime.now(UTC) - timedelta(hours=hours)
        result = await self.session.execute(
            select(TokenUsage)
            .where(TokenUsage.created_at >= since)
            .order_by(TokenUsage.created_at),
        )
        return [
            {
                "hour": u.created_at.isoformat(),
                "tokens": u.total_tokens,
                "cost": u.cost_usd,
                "provider": u.provider,
            }
            for u in result.scalars().all()
        ]
