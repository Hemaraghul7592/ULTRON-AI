from __future__ import annotations

from datetime import datetime  # noqa: TC003
from typing import Any
from uuid import uuid4

from pydantic import Field

from app.operations.domain.enums import ComponentType, EventType, HealthStatus
from app.operations.domain.models import (
    ComponentHealth,  # noqa: TC001
    DiagnosticPack,  # noqa: TC001
    EvidenceItem,  # noqa: TC001
    HealthSnapshot,  # noqa: TC001
    Incident,  # noqa: TC001
    MetricSample,  # noqa: TC001
)
from app.operations.domain.value_objects import DomainModel, utc_now


class DomainEvent(DomainModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: EventType
    occurred_at: datetime = Field(default_factory=utc_now)
    correlation_id: str | None = None
    causation_id: str | None = None
    source: str = Field(default="uaes", min_length=1, max_length=100)

    def payload(self) -> dict[str, Any]:
        return self.to_dict()


class HealthSnapshotRecorded(DomainEvent):
    event_type: EventType = EventType.HEALTH_SNAPSHOT_RECORDED
    snapshot: HealthSnapshot


class ComponentDegraded(DomainEvent):
    event_type: EventType = EventType.COMPONENT_DEGRADED
    component: ComponentHealth
    reason: str | None = None


class HealthCheckStarted(DomainEvent):
    event_type: EventType = EventType.HEALTH_CHECK_STARTED
    component_type: ComponentType
    component_name: str


class HealthCheckCompleted(DomainEvent):
    event_type: EventType = EventType.HEALTH_CHECK_COMPLETED
    component_type: ComponentType
    component_name: str
    status: HealthStatus
    score: float
    message: str


class ComponentStatus(DomainEvent):
    event_type: EventType = EventType.COMPONENT_HEALTHY
    component: ComponentHealth
    previous_status: HealthStatus | None = None


class IncidentCreated(DomainEvent):
    event_type: EventType = EventType.INCIDENT_CREATED
    incident: Incident


class IncidentResolved(DomainEvent):
    event_type: EventType = EventType.INCIDENT_RESOLVED
    incident: Incident


class EvidenceCollected(DomainEvent):
    event_type: EventType = EventType.EVIDENCE_COLLECTED
    evidence: EvidenceItem


class MetricsRecorded(DomainEvent):
    event_type: EventType = EventType.METRICS_RECORDED
    samples: list[MetricSample]


class DiagnosticPackGenerated(DomainEvent):
    event_type: EventType = EventType.DIAGNOSTIC_PACK_GENERATED
    pack: DiagnosticPack


class KnowledgeEntryCreated(DomainEvent):
    event_type: EventType = EventType.KNOWLEDGE_ENTRY_CREATED
    incident_id: str
    summary: str
    confidence: float


def event_from_dict(data: dict[str, Any]) -> DomainEvent:
    event_type = EventType(data["event_type"])
    event_map: dict[EventType, type[DomainEvent]] = {
        EventType.HEALTH_SNAPSHOT_RECORDED: HealthSnapshotRecorded,
        EventType.HEALTH_CHECK_STARTED: HealthCheckStarted,
        EventType.HEALTH_CHECK_COMPLETED: HealthCheckCompleted,
        EventType.COMPONENT_HEALTHY: ComponentStatus,
        EventType.COMPONENT_WARNING: ComponentStatus,
        EventType.COMPONENT_CRITICAL: ComponentStatus,
        EventType.COMPONENT_OFFLINE: ComponentStatus,
        EventType.COMPONENT_NOT_CONFIGURED: ComponentStatus,
        EventType.COMPONENT_DEGRADED: ComponentDegraded,
        EventType.INCIDENT_CREATED: IncidentCreated,
        EventType.INCIDENT_RESOLVED: IncidentResolved,
        EventType.EVIDENCE_COLLECTED: EvidenceCollected,
        EventType.METRICS_RECORDED: MetricsRecorded,
        EventType.DIAGNOSTIC_PACK_GENERATED: DiagnosticPackGenerated,
        EventType.KNOWLEDGE_ENTRY_CREATED: KnowledgeEntryCreated,
    }
    event_cls = event_map.get(event_type)
    if event_cls is None:
        return DomainEvent.model_validate(data)
    return event_cls.model_validate(data)
