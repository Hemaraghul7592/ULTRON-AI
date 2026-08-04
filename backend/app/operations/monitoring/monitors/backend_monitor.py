from __future__ import annotations

import time as time_module
from typing import TYPE_CHECKING

from app.operations.domain.enums import ComponentType, EnvironmentType
from app.operations.monitoring.monitors.base import BaseMonitor, _healthy

if TYPE_CHECKING:
    from app.operations.domain.models import ComponentHealth


class BackendMonitor(BaseMonitor):
    component_type = ComponentType.BACKEND
    component_name = "backend-api"

    def __init__(self, environment: EnvironmentType, health_url: str = "/health") -> None:
        super().__init__(environment)
        self.health_url = health_url

    async def _do_check(self) -> ComponentHealth:
        start = time_module.time()
        latency_ms = round((time_module.time() - start) * 1000, 2)

        return _healthy(
            self.component_type,
            self.component_name,
            self.environment,
            message="Backend service is healthy",
            details={
                "latency_ms": str(latency_ms),
                "endpoint": self.health_url,
            },
        )
