from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.operations.domain.enums import EventType, HealthStatus
from app.operations.domain.events import ComponentStatus, HealthCheckCompleted
from app.operations.infrastructure.db.repositories import SQLAlchemyHealthRepository
from app.operations.monitoring.aggregator import HealthAggregator
from app.operations.monitoring.factory import create_monitors
from app.operations.monitoring.scheduler import MonitoringScheduler

if TYPE_CHECKING:
    from collections.abc import Callable

    from app.operations.core.event_bus import EventBus
    from app.operations.core.runtime import OperationsRuntime
    from app.operations.domain.models import HealthSnapshot
    from app.operations.monitoring.interface import Monitor


def _status_to_event_type(status: HealthStatus) -> EventType:
    mapping: dict[HealthStatus, EventType] = {
        HealthStatus.HEALTHY: EventType.COMPONENT_HEALTHY,
        HealthStatus.WARNING: EventType.COMPONENT_WARNING,
        HealthStatus.CRITICAL: EventType.COMPONENT_CRITICAL,
        HealthStatus.OFFLINE: EventType.COMPONENT_OFFLINE,
        HealthStatus.NOT_CONFIGURED: EventType.COMPONENT_NOT_CONFIGURED,
    }
    return mapping.get(status, EventType.COMPONENT_DEGRADED)


async def _persist_and_publish(
    snapshot: HealthSnapshot,
    session_factory: Callable[[], Any],
    event_bus: EventBus,
) -> None:
    async with session_factory() as session:
        repository = SQLAlchemyHealthRepository(session)
        await repository.record_snapshot(snapshot)
        await session.commit()

    for component in snapshot.components:
        await event_bus.publish(
            HealthCheckCompleted(
                component_type=component.component_type,
                component_name=component.component_name,
                status=component.status,
                score=component.score,
                message=component.message,
            ),
        )
        event_type = _status_to_event_type(component.status)
        await event_bus.publish(
            ComponentStatus(
                event_type=event_type,
                component=component,
            ),
        )


async def setup_monitoring(runtime: OperationsRuntime) -> MonitoringScheduler:
    monitors: list[Monitor] = create_monitors()
    aggregator = HealthAggregator(monitors=monitors)
    runtime.monitors = monitors
    runtime.health_aggregator = aggregator

    async def _on_snapshot(snapshot: HealthSnapshot) -> None:
        await _persist_and_publish(snapshot, runtime.session_factory, runtime.event_bus)

    scheduler = MonitoringScheduler(
        aggregator=aggregator,
        interval_seconds=60.0,
        on_snapshot=_on_snapshot,
    )
    runtime.monitoring_scheduler = scheduler
    await scheduler.start()
    return scheduler
