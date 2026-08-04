from __future__ import annotations

import asyncio
import socket
from typing import TYPE_CHECKING

from app.operations.domain.enums import ComponentType, EnvironmentType
from app.operations.monitoring.monitors.base import (
    BaseMonitor,
    _healthy,
    _offline,
    _warning,
)

if TYPE_CHECKING:
    from app.operations.domain.models import ComponentHealth


class NetworkMonitor(BaseMonitor):
    component_type = ComponentType.NETWORK
    component_name = "network-connectivity"

    def __init__(
        self,
        environment: EnvironmentType,
        check_endpoints: list[tuple[str, int]] | None = None,
        timeout: float = 3.0,
    ) -> None:
        super().__init__(environment)
        self.check_endpoints = check_endpoints or [
            ("8.8.8.8", 53),
            ("1.1.1.1", 53),
        ]
        self.timeout = timeout

    async def _do_check(self) -> ComponentHealth:
        details: dict[str, str] = {}
        reachable_count = 0
        total_endpoints = len(self.check_endpoints)

        loop = asyncio.get_event_loop()
        for host, port in self.check_endpoints:
            try:
                await loop.run_in_executor(
                    None,
                    lambda h=host, p=port: socket.create_connection((h, p), timeout=self.timeout),
                )
                reachable_count += 1
                details[f"{host}:{port}"] = "reachable"
            except OSError:
                details[f"{host}:{port}"] = "unreachable"

        if reachable_count == 0:
            return _offline(
                self.component_type,
                self.component_name,
                self.environment,
                message="No network endpoints reachable",
                details=details,
            )
        if reachable_count < total_endpoints:
            return _warning(
                self.component_type,
                self.component_name,
                self.environment,
                message=(
                    f"Partial connectivity: {reachable_count}/{total_endpoints} endpoints reachable"
                ),
                score=(reachable_count / total_endpoints) * 100.0,
                details=details,
            )
        return _healthy(
            self.component_type,
            self.component_name,
            self.environment,
            message=f"All {total_endpoints} network endpoints reachable",
            details=details,
        )
