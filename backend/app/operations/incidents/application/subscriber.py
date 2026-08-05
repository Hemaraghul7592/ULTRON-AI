from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.operations.domain.enums import HealthStatus
from app.operations.domain.events import HealthCheckCompleted
from app.operations.incidents.application.investigation_service import (
    InvestigationService,
)
from app.operations.incidents.infrastructure.repositories import (
    SQLAlchemyIncidentRepositoryV3,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from app.operations.core.event_bus import EventBus, EventSubscription
    from app.operations.incidents.application.ports import (
        DiagnosticPackPort,
        EvidenceCollectorPort,
        InvestigationPublisher,
        RootCauseAnalysisPort,
    )
    from app.operations.incidents.domain.models import InvestigationResult

logger = logging.getLogger(__name__)

_TRIGGER_STATUSES = (HealthStatus.CRITICAL, HealthStatus.OFFLINE)


class IncidentInvestigationSubscriber:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        evidence_collector: EvidenceCollectorPort,
        root_cause_analyzer: RootCauseAnalysisPort,
        diagnostic_pack_generator: DiagnosticPackPort,
        publisher: InvestigationPublisher | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._evidence_collector = evidence_collector
        self._root_cause_analyzer = root_cause_analyzer
        self._diagnostic_pack_generator = diagnostic_pack_generator
        self._publisher = publisher
        self._subscription: EventSubscription | None = None

    def start(self, event_bus: EventBus) -> None:
        self._subscription = event_bus.subscribe(
            HealthCheckCompleted, self._on_health_check
        )

    def stop(self, event_bus: EventBus) -> None:
        if self._subscription is not None:
            event_bus.unsubscribe(self._subscription)
            self._subscription = None

    async def _on_health_check(self, event: HealthCheckCompleted) -> None:
        if event.status not in _TRIGGER_STATUSES:
            return
        try:
            await self._investigate(event)
        except Exception:
            logger.exception(
                "Incident investigation failed for component %s",
                event.component_name,
            )

    async def _investigate(
        self, event: HealthCheckCompleted
    ) -> InvestigationResult | None:
        async with self._session_factory() as session:
            repository = SQLAlchemyIncidentRepositoryV3(session)
            active = await repository.find_active_for_component(
                event.component_type.value, event.component_name
            )
            if active:
                logger.info(
                    "Active incident already exists for %s, skipping investigation",
                    event.component_name,
                )
                return None

            service = InvestigationService(
                repository=repository,
                evidence_collector=self._evidence_collector,
                root_cause_analyzer=self._root_cause_analyzer,
                diagnostic_pack_generator=self._diagnostic_pack_generator,
                publisher=self._publisher,
            )
            trigger = {
                "event_type": event.event_type.value,
                "component_type": event.component_type.value,
                "component_name": event.component_name,
                "status": event.status.value,
                "message": event.message,
                "source": "health_monitor",
            }
            result = await service.investigate(trigger)
            await session.commit()
            return result
