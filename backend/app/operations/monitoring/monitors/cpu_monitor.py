from __future__ import annotations

from typing import TYPE_CHECKING

from app.operations.domain.enums import ComponentType, EnvironmentType
from app.operations.monitoring.monitors.base import (
    BaseMonitor,
    _healthy,
    _not_configured,
    _warning,
)

if TYPE_CHECKING:
    from app.operations.domain.models import ComponentHealth


class CpuMonitor(BaseMonitor):
    component_type = ComponentType.CPU
    component_name = "system-cpu"

    def __init__(self, environment: EnvironmentType, warning_threshold: float = 80.0) -> None:
        super().__init__(environment)
        self.warning_threshold = warning_threshold

    async def _do_check(self) -> ComponentHealth:
        try:
            import psutil
        except ImportError:
            return _not_configured(
                self.component_type,
                self.component_name,
                self.environment,
                message="psutil not installed",
            )

        try:
            cpu_percent = psutil.cpu_percent(interval=1.0)
            if cpu_percent >= self.warning_threshold:
                return _warning(
                    self.component_type,
                    self.component_name,
                    self.environment,
                    message=f"CPU usage high: {cpu_percent}%",
                    score=max(0.0, 100.0 - cpu_percent),
                    details={
                        "cpu_percent": str(cpu_percent),
                        "threshold": str(self.warning_threshold),
                    },
                )
            return _healthy(
                self.component_type,
                self.component_name,
                self.environment,
                message=f"CPU usage normal: {cpu_percent}%",
                details={
                    "cpu_percent": str(cpu_percent),
                    "threshold": str(self.warning_threshold),
                },
            )
        except Exception as exc:  # noqa: BLE001
            return _not_configured(
                self.component_type,
                self.component_name,
                self.environment,
                message=f"CPU check failed: {exc}",
            )
