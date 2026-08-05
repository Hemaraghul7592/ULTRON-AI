from __future__ import annotations

from typing import TYPE_CHECKING

from app.operations.incidents.application.diagnostic_pack import DiagnosticPackGenerator
from app.operations.incidents.application.evidence_service import EvidenceCollectionService
from app.operations.incidents.application.publisher import InMemoryInvestigationPublisher
from app.operations.incidents.application.subscriber import IncidentInvestigationSubscriber
from app.operations.incidents.domain.analyzer import RootCauseAnalyzer
from app.operations.incidents.infrastructure.collectors import create_default_collectors

if TYPE_CHECKING:
    from app.operations.core.runtime import OperationsRuntime


async def setup_incident_investigation(
    runtime: OperationsRuntime,
) -> IncidentInvestigationSubscriber:
    collectors = create_default_collectors()
    evidence_service = EvidenceCollectionService(collectors=collectors)
    analyzer = RootCauseAnalyzer()
    pack_generator = DiagnosticPackGenerator()
    publisher = InMemoryInvestigationPublisher()

    subscriber = IncidentInvestigationSubscriber(
        session_factory=runtime.session_factory,
        evidence_collector=evidence_service,
        root_cause_analyzer=analyzer,
        diagnostic_pack_generator=pack_generator,
        publisher=publisher,
    )
    subscriber.start(runtime.event_bus)

    runtime.incident_subscriber = subscriber
    runtime.investigation_publisher = publisher
    return subscriber
