from __future__ import annotations

from datetime import datetime  # noqa: TC003
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.operations.incidents.domain.enums import (  # noqa: TC001
    EvidenceCategory,
    IncidentSeverity,
    IncidentStatus,
    RecommendedAction,
    RootCauseCategory,
)
from app.operations.incidents.domain.models import (  # noqa: TC001
    DiagnosticPack,
    Incident,
    IncidentEvidence,
    RecoveryRecommendation,
    RootCause,
)


class IncidentResponse(BaseModel):
    incident_id: str
    timestamp: datetime
    severity: IncidentSeverity
    component_type: str
    component_name: str
    environment: str
    summary: str
    detailed_description: str
    status: IncidentStatus
    triggered_by_event: str | None = None
    triggered_by_component: str | None = None
    triggered_at: datetime | None = None
    resolution: str | None = None
    confidence: float
    recovery_recommendation: str | None = None
    tags: dict[str, str] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_domain(cls, incident: Incident) -> IncidentResponse:
        return cls(
            incident_id=incident.incident_id,
            timestamp=incident.timestamp,
            severity=incident.severity,
            component_type=incident.component_type,
            component_name=incident.component_name,
            environment=incident.environment,
            summary=incident.summary,
            detailed_description=incident.detailed_description,
            status=incident.status,
            triggered_by_event=incident.triggered_by_event,
            triggered_by_component=incident.triggered_by_component,
            triggered_at=incident.triggered_at,
            resolution=incident.resolution,
            confidence=incident.confidence.value,
            recovery_recommendation=incident.recovery_recommendation,
            tags=dict(incident.tags),
        )


class IncidentEvidenceResponse(BaseModel):
    evidence_id: str
    incident_id: str
    category: EvidenceCategory
    source: str
    collected_at: datetime
    payload_ref: str
    redacted_excerpt: str
    checksum: str
    metadata: dict[str, str] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_domain(cls, evidence: IncidentEvidence) -> IncidentEvidenceResponse:
        return cls.model_validate(evidence)


class RootCauseResponse(BaseModel):
    root_cause_id: str
    incident_id: str
    category: RootCauseCategory
    description: str
    confidence: float
    supporting_evidence: list[str] = Field(default_factory=list)
    rule_matched: str
    determined_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_domain(cls, root_cause: RootCause) -> RootCauseResponse:
        return cls(
            root_cause_id=root_cause.root_cause_id,
            incident_id=root_cause.incident_id,
            category=root_cause.category,
            description=root_cause.description,
            confidence=root_cause.confidence.value,
            supporting_evidence=list(root_cause.supporting_evidence),
            rule_matched=root_cause.rule_matched,
            determined_at=root_cause.determined_at,
        )


class RecoveryRecommendationResponse(BaseModel):
    action: RecommendedAction
    description: str
    confidence: float
    estimated_impact: str
    prerequisites: list[str] = Field(default_factory=list)
    steps: list[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_domain(
        cls, recommendation: RecoveryRecommendation
    ) -> RecoveryRecommendationResponse:
        return cls(
            action=recommendation.action,
            description=recommendation.description,
            confidence=recommendation.confidence.value,
            estimated_impact=recommendation.estimated_impact,
            prerequisites=list(recommendation.prerequisites),
            steps=list(recommendation.steps),
        )


class DiagnosticPackResponse(BaseModel):
    pack_id: str
    incident_id: str
    generated_at: datetime
    summary: str
    timeline: list[dict[str, Any]] = Field(default_factory=list)
    health_snapshot: dict[str, Any] | None = None
    logs: list[str] = Field(default_factory=list)
    stack_traces: list[str] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)
    configuration: dict[str, Any] = Field(default_factory=dict)
    git_commit: str | None = None
    evidence_list: list[str] = Field(default_factory=list)
    root_cause: RootCauseResponse | None = None
    confidence_score: float
    recovery_recommendation: RecoveryRecommendationResponse | None = None

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_domain(cls, pack: DiagnosticPack) -> DiagnosticPackResponse:
        return cls(
            pack_id=pack.pack_id,
            incident_id=pack.incident_id,
            generated_at=pack.generated_at,
            summary=pack.summary,
            timeline=list(pack.timeline),
            health_snapshot=pack.health_snapshot,
            logs=list(pack.logs),
            stack_traces=list(pack.stack_traces),
            metrics=dict(pack.metrics),
            configuration=dict(pack.configuration),
            git_commit=pack.git_commit,
            evidence_list=list(pack.evidence_list),
            root_cause=None
            if pack.root_cause is None
            else RootCauseResponse.from_domain(pack.root_cause),
            confidence_score=pack.confidence_score.value,
            recovery_recommendation=None
            if pack.recovery_recommendation is None
            else RecoveryRecommendationResponse.from_domain(pack.recovery_recommendation),
        )


class IncidentCollectionResponse(BaseModel):
    incidents: list[IncidentResponse] = Field(default_factory=list)
    count: int = 0

    @classmethod
    def from_incidents(cls, incidents: list[Incident]) -> IncidentCollectionResponse:
        items = [IncidentResponse.from_domain(incident) for incident in incidents]
        return cls(incidents=items, count=len(items))


class EvidenceCollectionResponse(BaseModel):
    evidence: list[IncidentEvidenceResponse] = Field(default_factory=list)
    count: int = 0

    @classmethod
    def from_evidence(
        cls, evidence: list[IncidentEvidence]
    ) -> EvidenceCollectionResponse:
        items = [IncidentEvidenceResponse.from_domain(item) for item in evidence]
        return cls(evidence=items, count=len(items))


class IncidentDetailResponse(BaseModel):
    incident: IncidentResponse
    root_cause: RootCauseResponse | None = None
    diagnostic_pack: DiagnosticPackResponse | None = None
    evidence_count: int = 0


class InvestigateRequest(BaseModel):
    component_type: str = Field(default="unknown", max_length=30)
    component_name: str = Field(default="unknown", max_length=100)
    environment: str = Field(default="production", max_length=20)
    message: str = Field(default="", max_length=5000)
    status: str = Field(default="critical", max_length=30)


class InvestigationResponse(BaseModel):
    incident_id: str
    status: str
    root_cause: RootCauseResponse | None = None
    recovery_recommendation: RecoveryRecommendationResponse | None = None
    evidence_count: int = 0
    duration_ms: int = 0
    errors: list[str] = Field(default_factory=list)
