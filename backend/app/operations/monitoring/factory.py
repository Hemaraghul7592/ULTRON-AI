from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.config import get_settings
from app.operations.domain.enums import EnvironmentType
from app.operations.monitoring.monitors import (
    BackendMonitor,
    CpuMonitor,
    DatabaseMonitor,
    DiskMonitor,
    DockerMonitor,
    GithubMonitor,
    MemoryMonitor,
    NetworkMonitor,
    RedisMonitor,
)

if TYPE_CHECKING:
    from app.operations.monitoring.interface import Monitor


def default_environment() -> EnvironmentType:
    env = get_settings().DEBUG
    if env:
        return EnvironmentType.DEVELOPMENT
    return EnvironmentType.PRODUCTION


def create_monitors(environment: EnvironmentType | None = None) -> list[Monitor]:
    env = environment or default_environment()
    return [
        DatabaseMonitor(environment=env),
        RedisMonitor(environment=env),
        BackendMonitor(environment=env),
        DockerMonitor(environment=env),
        GithubMonitor(environment=env),
        CpuMonitor(environment=env),
        MemoryMonitor(environment=env),
        DiskMonitor(environment=env),
        NetworkMonitor(environment=env),
    ]
