from __future__ import annotations

import shutil
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


class DiskMonitor(BaseMonitor):
    component_type = ComponentType.DISK
    component_name = "system-disk"

    def __init__(
        self,
        environment: EnvironmentType,
        warning_threshold: float = 90.0,
        path: str = "/",
    ) -> None:
        super().__init__(environment)
        self.warning_threshold = warning_threshold
        self.path = path

    async def _do_check(self) -> ComponentHealth:
        try:
            usage = shutil.disk_usage(self.path)
            disk_percent = (usage.used / usage.total) * 100.0
            if disk_percent >= self.warning_threshold:
                return _warning(
                    self.component_type,
                    self.component_name,
                    self.environment,
                    message=f"Disk usage high: {disk_percent:.1f}%",
                    score=max(0.0, 100.0 - disk_percent),
                    details={
                        "disk_percent": f"{disk_percent:.1f}",
                        "threshold": str(self.warning_threshold),
                        "path": self.path,
                        "total_bytes": str(usage.total),
                        "used_bytes": str(usage.used),
                        "free_bytes": str(usage.free),
                    },
                )
            return _healthy(
                self.component_type,
                self.component_name,
                self.environment,
                message=f"Disk usage normal: {disk_percent:.1f}%",
                details={
                    "disk_percent": f"{disk_percent:.1f}",
                    "threshold": str(self.warning_threshold),
                    "path": self.path,
                    "total_bytes": str(usage.total),
                },
            )
        except Exception as exc:  # noqa: BLE001
            return _not_configured(
                self.component_type,
                self.component_name,
                self.environment,
                message=f"Disk check failed: {exc}",
            )
