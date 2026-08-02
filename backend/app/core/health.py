from __future__ import annotations

from typing import Any

from sqlalchemy import text

from app.core.config import get_settings
from app.core.database import get_engine
from app.core.logging import get_logger

logger = get_logger(__name__)


async def check_database() -> dict[str, Any]:
    eng = get_engine()
    if eng is None:
        return {"status": "unavailable", "detail": "not initialized"}
    try:
        async with eng.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "healthy"}
    except Exception as e:
        logger.error("health_db_failed", error=str(e))
        return {"status": "unhealthy", "detail": "Database health check failed"}


async def check_redis() -> dict[str, Any]:
    settings = get_settings()
    if not settings.REDIS_URL:
        return {"status": "not_configured"}
    try:
        import redis.asyncio as aioredis

        r = aioredis.from_url(settings.REDIS_URL, decode_responses=True, socket_connect_timeout=2)
        await r.ping()
        await r.aclose()
        return {"status": "healthy"}
    except Exception as e:
        logger.warning("health_redis_failed", error=str(e))
        return {"status": "unhealthy", "detail": "Redis health check failed"}


async def get_health() -> dict[str, Any]:
    db_status = await check_database()
    redis_status = await check_redis()
    all_healthy = db_status["status"] == "healthy" and redis_status["status"] in (
        "healthy",
        "not_configured",
    )
    return {
        "status": "healthy" if all_healthy else "degraded",
        "version": get_settings().APP_VERSION,
        "service": "ultron-backend",
        "checks": {
            "database": db_status,
            "redis": redis_status,
        },
    }
