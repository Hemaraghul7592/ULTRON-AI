from __future__ import annotations

from datetime import datetime  # noqa: TC003

from pydantic import BaseModel, ConfigDict, Field

from app.operations.domain.enums import (  # noqa: TC001
    ComponentType,
    EnvironmentType,
    EvidenceType,
    HealthStatus,
    IncidentSeverity,
    IncidentStatus,
    MetricType,
)
from app.operations.domain.models import (  # noqa: TC001
    ComponentHealth,
    DiagnosticPack,
    EvidenceItem,
    HealthSnapshot,
    Incident,
    MetricSample,
)


class EvidenceItemResponse(BaseModel):
    evidence_id: str
    incident_id: str
    evidence_type: EvidenceType
    source: str
    collected_at: datetime
    payload_ref: str
    redacted_excerpt: str
    checksum: str
    metadata: dict[str, str] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_domain(cls, evidence: EvidenceItem) -> EvidenceItemResponse:
        return cls.model_validate(evidence)


class ComponentHealthResponse(BaseModel):
    component_id: str
    component_type: ComponentType
    component_name: str
    environment: EnvironmentType
    status: HealthStatus
    score: float
    message: str
    observed_at: datetime
    details: dict[str, str] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_domain(cls, component: ComponentHealth) -> ComponentHealthResponse:
        return cls.model_validate(component)


class HealthSnapshotResponse(BaseModel):
    snapshot_id: str
    environment: EnvironmentType
    overall_status: HealthStatus
    overall_score: float
    collected_at: datetime
    components: list[ComponentHealthResponse] = Field(default_factory=list)
    source: str

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_domain(cls, snapshot: HealthSnapshot) -> HealthSnapshotResponse:
        return cls(
            snapshot_id=snapshot.snapshot_id,
            environment=snapshot.environment,
            overall_status=snapshot.overall_status,
            overall_score=snapshot.overall_score,
            collected_at=snapshot.collected_at,
            components=[
                ComponentHealthResponse.from_domain(component) for component in snapshot.components
            ],
            source=snapshot.source,
        )


class HealthOverviewResponse(BaseModel):
    overall_status: HealthStatus = HealthStatus.HEALTHY
    snapshots: list[HealthSnapshotResponse] = Field(default_factory=list)
    components: list[ComponentHealthResponse] = Field(default_factory=list)

    @classmethod
    def from_snapshot(cls, snapshot: HealthSnapshot | None) -> HealthOverviewResponse:
        if snapshot is None:
            return cls()
        return cls(
            overall_status=snapshot.overall_status,
            snapshots=[HealthSnapshotResponse.from_domain(snapshot)],
            components=[
                ComponentHealthResponse.from_domain(component) for component in snapshot.components
            ],
        )


class IncidentResponse(BaseModel):
    incident_id: str
    timestamp: datetime
    severity: IncidentSeverity
    component: ComponentType
    environment: EnvironmentType
    summary: str
    detailed_description: str
    evidence: list[EvidenceItemResponse] = Field(default_factory=list)
    status: IncidentStatus
    resolution: str | None = None
    confidence: float
    recovery_plan: str | None = None
    duration_seconds: float | None = None
    risk: float | None = None

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_domain(cls, incident: Incident) -> IncidentResponse:
        return cls(
            incident_id=incident.incident_id,
            timestamp=incident.timestamp,
            severity=incident.severity,
            component=incident.component,
            environment=incident.environment,
            summary=incident.summary,
            detailed_description=incident.detailed_description,
            evidence=[EvidenceItemResponse.from_domain(item) for item in incident.evidence],
            status=incident.status,
            resolution=incident.resolution,
            confidence=incident.confidence.value,
            recovery_plan=incident.recovery_plan,
            duration_seconds=None
            if incident.duration is None
            else incident.duration.total_seconds(),
            risk=None if incident.risk is None else incident.risk.value,
        )


class IncidentCollectionResponse(BaseModel):
    incidents: list[IncidentResponse] = Field(default_factory=list)
    total: int = 0

    @classmethod
    def from_domain(cls, incidents: list[Incident]) -> IncidentCollectionResponse:
        return cls(
            incidents=[IncidentResponse.from_domain(incident) for incident in incidents],
            total=len(incidents),
        )


class MetricSampleResponse(BaseModel):
    metric_id: str
    metric_type: MetricType
    name: str
    value: float
    unit: str | None = None
    component: ComponentType | None = None
    environment: EnvironmentType
    source: str
    observed_at: datetime
    tags: dict[str, str] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_domain(cls, metric: MetricSample) -> MetricSampleResponse:
        return cls.model_validate(metric)


class MetricsCollectionResponse(BaseModel):
    metrics: list[MetricSampleResponse] = Field(default_factory=list)
    total: int = 0

    @classmethod
    def from_domain(cls, metrics: list[MetricSample]) -> MetricsCollectionResponse:
        return cls(
            metrics=[MetricSampleResponse.from_domain(metric) for metric in metrics],
            total=len(metrics),
        )


class DiagnosticPackResponse(BaseModel):
    pack_id: str
    incident_id: str
    generated_at: datetime
    summary: str
    log_ref: str | None = None
    metric_ref: str | None = None
    config_ref: str | None = None
    environment_ref: str | None = None
    commit_ref: str | None = None
    evidence: list[EvidenceItemResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_domain(cls, pack: DiagnosticPack) -> DiagnosticPackResponse:
        return cls(
            pack_id=pack.pack_id,
            incident_id=pack.incident_id,
            generated_at=pack.generated_at,
            summary=pack.summary,
            log_ref=pack.log_ref,
            metric_ref=pack.metric_ref,
            config_ref=pack.config_ref,
            environment_ref=pack.environment_ref,
            commit_ref=pack.commit_ref,
            evidence=[EvidenceItemResponse.from_domain(item) for item in pack.evidence],
        )


class DiagnosticsCollectionResponse(BaseModel):
    diagnostic_packs: list[DiagnosticPackResponse] = Field(default_factory=list)
    total: int = 0

    @classmethod
    def from_domain(cls, diagnostic_packs: list[DiagnosticPack]) -> DiagnosticsCollectionResponse:
        return cls(
            diagnostic_packs=[
                DiagnosticPackResponse.from_domain(pack) for pack in diagnostic_packs
            ],
            total=len(diagnostic_packs),
        )
