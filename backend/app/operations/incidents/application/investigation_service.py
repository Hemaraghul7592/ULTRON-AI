from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from app.operations.domain.value_objects import utc_now
from app.operations.incidents.domain.enums import (
    IncidentSeverity,
    IncidentStatus,
    InvestigationStatus,
    RootCauseCategory,
)
from app.operations.incidents.domain.events import (
    IncidentDetected,
    InvestigationCompleted,
    InvestigationStarted,
)
from app.operations.incidents.domain.models import (
    Incident,
    InvestigationResult,
)

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from app.operations.incidents.application.ports import (
        DiagnosticPackPort,
        EvidenceCollectorPort,
        IncidentRepository,
        InvestigationPublisher,
        RootCauseAnalysisPort,
    )

_TRIGGER_SEVERITY_MAP: dict[str, IncidentSeverity] = {
    "critical": IncidentSeverity.CRITICAL,
    "offline": IncidentSeverity.EMERGENCY,
    "warning": IncidentSeverity.WARNING,
    "degraded": IncidentSeverity.HIGH,
}


class InvestigationService:
    def __init__(
        self,
        repository: IncidentRepository,
        evidence_collector: EvidenceCollectorPort,
        root_cause_analyzer: RootCauseAnalysisPort,
        diagnostic_pack_generator: DiagnosticPackPort,
        publisher: InvestigationPublisher | None = None,
    ) -> None:
        self._repository = repository
        self._evidence_collector = evidence_collector
        self._root_cause_analyzer = root_cause_analyzer
        self._diagnostic_pack_generator = diagnostic_pack_generator
        self._publisher = publisher

    async def investigate(self, trigger: dict[str, Any]) -> InvestigationResult:
        incident = self._create_incident(trigger)
        await self._repository.save(incident)
        await self._publish(
            IncidentDetected(
                incident=incident,
                trigger_event_type=trigger.get("event_type"),
            )
        )

        started_at = utc_now()
        investigation_id = str(uuid4())
        await self._publish(
            InvestigationStarted(
                incident_id=incident.incident_id,
                investigation_id=investigation_id,
            )
        )

        try:
            bundle = await self._evidence_collector.collect_evidence(incident)
            incident = incident.model_copy(
                update={"status": IncidentStatus.EVIDENCE_COLLECTED}
            )
            await self._repository.save(incident)
            if bundle.evidence:
                await self._repository.add_evidence(incident.incident_id, bundle.evidence)

            root_cause = self._root_cause_analyzer.analyze(incident, bundle)
            recovery = self._root_cause_analyzer.recommend_recovery(root_cause)
            await self._repository.add_root_cause(incident.incident_id, root_cause)

            pack = self._diagnostic_pack_generator.generate(
                incident, bundle, root_cause, recovery
            )
            await self._repository.add_diagnostic_pack(incident.incident_id, pack)

            root_cause_known = root_cause.category != RootCauseCategory.UNKNOWN
            final_status = (
                IncidentStatus.ROOT_CAUSE_FOUND
                if root_cause_known
                else IncidentStatus.WAITING_FOR_REPAIR
            )
            incident = incident.model_copy(
                update={
                    "status": final_status,
                    "confidence": root_cause.confidence,
                    "recovery_recommendation": recovery.description,
                }
            )
            await self._repository.save(incident)

            completed_at = utc_now()
            result = InvestigationResult(
                investigation_id=investigation_id,
                incident_id=incident.incident_id,
                status=InvestigationStatus.COMPLETED,
                evidence_bundle=bundle,
                root_cause=root_cause,
                recovery_recommendation=recovery,
                diagnostic_pack=pack,
                started_at=started_at,
                completed_at=completed_at,
                duration_ms=int((completed_at - started_at).total_seconds() * 1000),
            )
        except Exception as exc:
            logger.exception("Investigation failed for incident %s", incident.incident_id)
            incident = incident.model_copy(update={"status": IncidentStatus.FAILED})
            await self._repository.save(incident)
            completed_at = utc_now()
            result = InvestigationResult(
                investigation_id=investigation_id,
                incident_id=incident.incident_id,
                status=InvestigationStatus.FAILED,
                started_at=started_at,
                completed_at=completed_at,
                duration_ms=int((completed_at - started_at).total_seconds() * 1000),
                errors=[str(exc)],
            )

        await self._publish(InvestigationCompleted(investigation_result=result))
        return result

    def _create_incident(self, trigger: dict[str, Any]) -> Incident:
        component_type = trigger.get("component_type", "unknown")
        component_name = trigger.get("component_name", "unknown")
        status_hint = str(trigger.get("status", "")).lower()
        severity = _TRIGGER_SEVERITY_MAP.get(status_hint, IncidentSeverity.HIGH)
        message = trigger.get("message") or trigger.get("error_details") or ""
        summary = f"{component_name} {status_hint or 'incident'}".strip()[:200]
        description = (
            message
            or f"Incident triggered for component {component_name} ({component_type})"
        )[:5000]

        return Incident(
            severity=severity,
            component_type=component_type,
            component_name=component_name,
            environment=trigger.get("environment", "production"),
            summary=summary,
            detailed_description=description,
            status=IncidentStatus.DETECTED,
            triggered_by_event=trigger.get("event_type"),
            triggered_by_component=component_name,
            triggered_at=utc_now(),
            tags={"source": trigger.get("source", "manual")},
        )

    async def _publish(self, event: Any) -> None:
        if self._publisher is None:
            return
        try:
            await self._publisher.publish(event)
        except Exception:
            logger.exception("Failed to publish incident event %s", event.event_type)
