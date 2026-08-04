from __future__ import annotations

import time as time_module
from typing import TYPE_CHECKING

from sqlalchemy import text

from app.core.database import get_engine
from app.operations.domain.enums import ComponentType, EnvironmentType
from app.operations.monitoring.monitors.base import (
    BaseMonitor,
    _healthy,
    _not_configured,
    _offline,
)

if TYPE_CHECKING:
    from app.operations.domain.models import ComponentHealth


class DatabaseMonitor(BaseMonitor):
    component_type = ComponentType.DATABASE
    component_name = "primary-db"

    def __init__(self, environment: EnvironmentType, database_url: str | None = None) -> None:
        super().__init__(environment)
        self.database_url = database_url

    async def _do_check(self) -> ComponentHealth:
        engine = get_engine()
        if engine is None:
            return _not_configured(
                self.component_type,
                self.component_name,
                self.environment,
                message="Database engine not initialized",
            )

        start = time_module.time()
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
                latency_ms = round((time_module.time() - start) * 1000, 2)
                return _healthy(
                    self.component_type,
                    self.component_name,
                    self.environment,
                    message="Database is responsive",
                    details={
                        "latency_ms": str(latency_ms),
                        "url": self.database_url or "default",
                    },
                )
        except Exception as exc:  # noqa: BLE001
            return _offline(
                self.component_type,
                self.component_name,
                self.environment,
                message=f"Database check failed: {exc}",
                details={"error": str(exc)},
            )
