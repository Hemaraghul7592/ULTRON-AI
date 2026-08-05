from __future__ import annotations

from typing import TYPE_CHECKING

from app.operations.incidents.infrastructure.collectors.config_collectors import (
    ConfigCollector,
    EnvironmentVariableCollector,
    GitCommitCollector,
    GitDiffCollector,
    HealthSnapshotCollector,
    MetricsSnapshotCollector,
    StartupSequenceCollector,
)
from app.operations.incidents.infrastructure.collectors.log_collectors import (
    FastAPILogCollector,
    SchedulerLogCollector,
    StackTraceCollector,
    StructuredLogCollector,
)
from app.operations.incidents.infrastructure.collectors.system_collectors import (
    CpuStatusCollector,
    DatabaseStatusCollector,
    DiskStatusCollector,
    DiStateCollector,
    DockerStatusCollector,
    GithubActionsLogCollector,
    MemoryStatusCollector,
    NetworkStatusCollector,
    RedisStatusCollector,
    RunningTasksCollector,
)

if TYPE_CHECKING:
    from app.operations.incidents.infrastructure.collectors.base import EvidenceCollector


def create_default_collectors() -> list[EvidenceCollector]:
    return [
        FastAPILogCollector(),
        StackTraceCollector(),
        StructuredLogCollector(),
        SchedulerLogCollector(),
        HealthSnapshotCollector(),
        MetricsSnapshotCollector(),
        GitCommitCollector(),
        GitDiffCollector(),
        EnvironmentVariableCollector(),
        ConfigCollector(),
        StartupSequenceCollector(),
        DockerStatusCollector(),
        RedisStatusCollector(),
        DatabaseStatusCollector(),
        CpuStatusCollector(),
        MemoryStatusCollector(),
        DiskStatusCollector(),
        NetworkStatusCollector(),
        RunningTasksCollector(),
        DiStateCollector(),
        GithubActionsLogCollector(),
    ]
