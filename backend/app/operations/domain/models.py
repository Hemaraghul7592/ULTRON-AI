from __future__ import annotations

from datetime import datetime, timedelta  # noqa: TC003

from pydantic import Field

from app.operations.domain.enums import (
    ComponentType,
    EnvironmentType,
    EvidenceType,
    HealthStatus,
    IncidentSeverity,
    IncidentStatus,
    MetricType,
)
from app.operations.domain.value_objects import ConfidenceScore, DomainModel, RiskScore, utc_now


class EvidenceItem(DomainModel):
    evidence_id: str
    incident_id: str
    evidence_type: EvidenceType
    source: str = Field(..., min_length=1, max_length=100)
    collected_at: datetime = Field(default_factory=utc_now)
    payload_ref: str = Field(..., min_length=1, max_length=255)
    redacted_excerpt: str = Field(..., min_length=1, max_length=4000)
    checksum: str = Field(..., min_length=8, max_length=128)
    metadata: dict[str, str] = Field(default_factory=dict)


class ComponentHealth(DomainModel):
    component_id: str
    component_type: ComponentType
    component_name: str = Field(..., min_length=1, max_length=100)
    environment: EnvironmentType
    status: HealthStatus
    score: float = Field(..., ge=0.0, le=100.0)
    message: str = Field(..., min_length=1, max_length=500)
    observed_at: datetime = Field(default_factory=utc_now)
    details: dict[str, str] = Field(default_factory=dict)


class HealthSnapshot(DomainModel):
    snapshot_id: str
    environment: EnvironmentType
    overall_status: HealthStatus
    overall_score: float = Field(..., ge=0.0, le=100.0)
    collected_at: datetime = Field(default_factory=utc_now)
    components: list[ComponentHealth] = Field(default_factory=list)
    source: str = Field(default="uaes-monitoring", min_length=1, max_length=100)


class Incident(DomainModel):
    incident_id: str
    timestamp: datetime = Field(default_factory=utc_now)
    severity: IncidentSeverity
    component: ComponentType
    environment: EnvironmentType
    summary: str = Field(..., min_length=1, max_length=200)
    detailed_description: str = Field(..., min_length=1, max_length=5000)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    status: IncidentStatus = IncidentStatus.OPEN
    resolution: str | None = Field(default=None, max_length=4000)
    confidence: ConfidenceScore = Field(default_factory=lambda: ConfidenceScore(value=0.0))
    recovery_plan: str | None = Field(default=None, max_length=4000)
    duration: timedelta | None = None
    risk: RiskScore | None = None


class MetricSample(DomainModel):
    metric_id: str
    metric_type: MetricType
    name: str = Field(..., min_length=1, max_length=100)
    value: float
    unit: str | None = Field(default=None, max_length=20)
    component: ComponentType | None = None
    environment: EnvironmentType
    source: str = Field(..., min_length=1, max_length=100)
    observed_at: datetime = Field(default_factory=utc_now)
    tags: dict[str, str] = Field(default_factory=dict)


class DiagnosticPack(DomainModel):
    pack_id: str
    incident_id: str
    generated_at: datetime = Field(default_factory=utc_now)
    summary: str = Field(..., min_length=1, max_length=1000)
    log_ref: str | None = Field(default=None, max_length=255)
    metric_ref: str | None = Field(default=None, max_length=255)
    config_ref: str | None = Field(default=None, max_length=255)
    environment_ref: str | None = Field(default=None, max_length=255)
    commit_ref: str | None = Field(default=None, max_length=255)
    evidence: list[EvidenceItem] = Field(default_factory=list)
