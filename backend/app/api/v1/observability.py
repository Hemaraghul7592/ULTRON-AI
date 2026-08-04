from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.v1.auth import require_admin, verify_token
from app.core.database import get_session
from app.observability.dashboard import DashboardService
from app.observability.metrics import MetricsService

router = APIRouter(
    prefix="/observability", tags=["observability"], dependencies=[Depends(verify_token)],
)


@router.get("/dashboard")
async def get_dashboard(user: dict = Depends(verify_token)) -> dict:  # noqa: B008 FastAPI Depends() convention
    user_id = user["user_id"]
    session_factory = get_session()
    async with session_factory() as session:
        dashboard = DashboardService(session)
        return await dashboard.get_dashboard(user_id=user_id)


@router.get("/metrics")
async def get_metrics(
    limit: int = Query(50, ge=1, le=500), _: dict = Depends(require_admin),  # noqa: B008 FastAPI Depends() convention
) -> list[dict]:
    session_factory = get_session()
    async with session_factory() as session:
        metrics = MetricsService(session)
        recent = await metrics.get_recent_metrics(limit=limit)
        return [
            {
                "id": m.id,
                "name": m.name,
                "value": m.value,
                "unit": m.unit,
                "source": m.source,
                "created_at": m.created_at.isoformat(),
            }
            for m in recent
        ]


@router.get("/metrics/latency")
async def get_latency(
    hours: int = Query(24, ge=1, le=168), _: dict = Depends(require_admin),  # noqa: B008 FastAPI Depends() convention
) -> dict:
    session_factory = get_session()
    async with session_factory() as session:
        metrics = MetricsService(session)
        return await metrics.get_latency_percentiles(hours=hours)


@router.get("/metrics/tokens")
async def get_token_usage(
    hours: int = Query(24, ge=1, le=168), _: dict = Depends(require_admin),  # noqa: B008 FastAPI Depends() convention
) -> dict:
    session_factory = get_session()
    async with session_factory() as session:
        metrics = MetricsService(session)
        totals = await metrics.get_token_totals(hours=hours)
        providers = await metrics.get_ai_usage(hours=hours)
        return {
            "totals": totals,
            "by_provider": providers,
        }
