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


class MemoryMonitor(BaseMonitor):
    component_type = ComponentType.MEMORY
    component_name = "system-memory"

    def __init__(self, environment: EnvironmentType, warning_threshold: float = 85.0) -> None:
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
            vm = psutil.virtual_memory()
            memory_percent = vm.percent
            if memory_percent >= self.warning_threshold:
                return _warning(
                    self.component_type,
                    self.component_name,
                    self.environment,
                    message=f"Memory usage high: {memory_percent}%",
                    score=max(0.0, 100.0 - memory_percent),
                    details={
                        "memory_percent": str(memory_percent),
                        "threshold": str(self.warning_threshold),
                        "total_bytes": str(vm.total),
                        "available_bytes": str(vm.available),
                    },
                )
            return _healthy(
                self.component_type,
                self.component_name,
                self.environment,
                message=f"Memory usage normal: {memory_percent}%",
                details={
                    "memory_percent": str(memory_percent),
                    "threshold": str(self.warning_threshold),
                    "total_bytes": str(vm.total),
                },
            )
        except Exception as exc:  # noqa: BLE001
            return _not_configured(
                self.component_type,
                self.component_name,
                self.environment,
                message=f"Memory check failed: {exc}",
            )
