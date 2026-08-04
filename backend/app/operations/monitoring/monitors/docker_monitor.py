from __future__ import annotations

from typing import TYPE_CHECKING

from app.operations.domain.enums import ComponentType
from app.operations.monitoring.monitors.base import (
    BaseMonitor,
    _healthy,
    _not_configured,
)

if TYPE_CHECKING:
    from app.operations.domain.models import ComponentHealth


class DockerMonitor(BaseMonitor):
    component_type = ComponentType.DOCKER
    component_name = "docker-daemon"

    async def _do_check(self) -> ComponentHealth:
        try:
            import docker
        except ImportError:
            return _not_configured(
                self.component_type,
                self.component_name,
                self.environment,
                message="Docker SDK not installed",
            )

        try:
            client = docker.from_env()
            client.ping()
            return _healthy(
                self.component_type,
                self.component_name,
                self.environment,
                message="Docker daemon is reachable",
            )
        except Exception:
            return _not_configured(
                self.component_type,
                self.component_name,
                self.environment,
                message="Docker daemon not available",
            )
