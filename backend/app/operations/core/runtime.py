from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker  # noqa: TC002

from app.operations.core.event_bus import EventBus  # noqa: TC001
from app.operations.monitoring.aggregator import HealthAggregator  # noqa: TC001
from app.operations.monitoring.interface import Monitor  # noqa: TC001
from app.operations.monitoring.scheduler import MonitoringScheduler  # noqa: TC001


@dataclass(slots=True)
class OperationsRuntime:
    event_bus: EventBus
    session_factory: async_sessionmaker[AsyncSession]
    monitors: list[Monitor] = field(default_factory=list)
    health_aggregator: HealthAggregator | None = None
    monitoring_scheduler: MonitoringScheduler | None = None
