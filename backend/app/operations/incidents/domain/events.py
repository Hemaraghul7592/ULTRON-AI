from __future__ import annotations

from datetime import datetime  # noqa: TC003
from typing import Any
from uuid import uuid4

from pydantic import Field

from app.operations.domain.value_objects import DomainModel, utc_now
from app.operations.incidents.domain.models import (  # noqa: TC001
    Incident,
    IncidentEvidence,
    InvestigationResult,
    RootCause,
)


class IncidentDomainEvent(DomainModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str
    occurred_at: datetime = Field(default_factory=utc_now)
    correlation_id: str | None = None
    causation_id: str | None = None
    source: str = Field(default="uaes-incidents", min_length=1, max_length=100)

    def payload(self) -> dict[str, Any]:
        return self.to_dict()


class IncidentDetected(IncidentDomainEvent):
    event_type: str = "incident_detected"
    incident: Incident
    trigger_event_type: str | None = None


class InvestigationStarted(IncidentDomainEvent):
    event_type: str = "investigation_started"
    incident_id: str
    investigation_id: str


class EvidenceCollected(IncidentDomainEvent):
    event_type: str = "evidence_collected"
    incident_id: str
    evidence: IncidentEvidence


class EvidenceCollectionFailed(IncidentDomainEvent):
    event_type: str = "evidence_collection_failed"
    incident_id: str
    collector_name: str
    error: str


class RootCauseDetermined(IncidentDomainEvent):
    event_type: str = "root_cause_determined"
    incident_id: str
    root_cause: RootCause


class InvestigationCompleted(IncidentDomainEvent):
    event_type: str = "investigation_completed"
    investigation_result: InvestigationResult


def incident_event_from_dict(data: dict[str, Any]) -> IncidentDomainEvent:
    event_type = data["event_type"]
    event_map: dict[str, type[IncidentDomainEvent]] = {
        "incident_detected": IncidentDetected,
        "investigation_started": InvestigationStarted,
        "evidence_collected": EvidenceCollected,
        "evidence_collection_failed": EvidenceCollectionFailed,
        "root_cause_determined": RootCauseDetermined,
        "investigation_completed": InvestigationCompleted,
    }
    event_cls = event_map.get(event_type)
    if event_cls is None:
        return IncidentDomainEvent.model_validate(data)
    return event_cls.model_validate(data)
