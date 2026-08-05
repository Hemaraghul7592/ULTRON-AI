from __future__ import annotations

from datetime import datetime, timedelta  # noqa: TC003
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from app.operations.domain.value_objects import ConfidenceScore, RiskScore, utc_now
from app.operations.incidents.domain.enums import (
    EvidenceCategory,
    IncidentSeverity,
    IncidentStatus,
    InvestigationStatus,
    RecommendedAction,
    RootCauseCategory,
)


class Incident(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    incident_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=utc_now)
    severity: IncidentSeverity
    component_type: str
    component_name: str
    environment: str
    summary: str = Field(..., min_length=1, max_length=200)
    detailed_description: str = Field(..., min_length=1, max_length=5000)
    status: IncidentStatus = IncidentStatus.DETECTED
    triggered_by_event: str | None = None
    triggered_by_component: str | None = None
    triggered_at: datetime | None = None
    resolution: str | None = Field(default=None, max_length=4000)
    confidence: ConfidenceScore = Field(default_factory=lambda: ConfidenceScore(value=0.0))
    recovery_recommendation: str | None = Field(default=None, max_length=4000)
    duration: timedelta | None = None
    risk: RiskScore | None = None
    tags: dict[str, str] = Field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Incident:
        return cls.model_validate(data)


class IncidentEvidence(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    evidence_id: str = Field(default_factory=lambda: str(uuid4()))
    incident_id: str
    category: EvidenceCategory
    source: str = Field(..., min_length=1, max_length=100)
    collected_at: datetime = Field(default_factory=utc_now)
    payload_ref: str = Field(..., min_length=1, max_length=255)
    redacted_excerpt: str = Field(..., min_length=1, max_length=4000)
    checksum: str = Field(..., min_length=8, max_length=128)
    metadata: dict[str, str] = Field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> IncidentEvidence:
        return cls.model_validate(data)


class EvidenceBundle(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    bundle_id: str = Field(default_factory=lambda: str(uuid4()))
    incident_id: str
    collected_at: datetime = Field(default_factory=utc_now)
    evidence: list[IncidentEvidence] = Field(default_factory=list)
    collection_duration_ms: int = 0
    failed_collectors: list[str] = Field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EvidenceBundle:
        return cls.model_validate(data)


class RootCause(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    root_cause_id: str = Field(default_factory=lambda: str(uuid4()))
    incident_id: str
    category: RootCauseCategory
    description: str = Field(..., min_length=1, max_length=1000)
    confidence: ConfidenceScore
    supporting_evidence: list[str] = Field(default_factory=list)
    rule_matched: str = Field(..., min_length=1, max_length=200)
    determined_at: datetime = Field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RootCause:
        return cls.model_validate(data)


class RecoveryRecommendation(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    action: RecommendedAction
    description: str = Field(..., min_length=1, max_length=1000)
    confidence: ConfidenceScore
    estimated_impact: str = Field(..., min_length=1, max_length=200)
    prerequisites: list[str] = Field(default_factory=list)
    steps: list[str] = Field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RecoveryRecommendation:
        return cls.model_validate(data)


class DiagnosticPack(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    pack_id: str = Field(default_factory=lambda: str(uuid4()))
    incident_id: str
    generated_at: datetime = Field(default_factory=utc_now)
    summary: str = Field(..., min_length=1, max_length=1000)
    timeline: list[dict[str, Any]] = Field(default_factory=list)
    health_snapshot: dict[str, Any] | None = None
    logs: list[str] = Field(default_factory=list)
    stack_traces: list[str] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)
    configuration: dict[str, Any] = Field(default_factory=dict)
    git_commit: str | None = None
    evidence_list: list[str] = Field(default_factory=list)
    root_cause: RootCause | None = None
    confidence_score: ConfidenceScore = Field(default_factory=lambda: ConfidenceScore(value=0.0))
    recovery_recommendation: RecoveryRecommendation | None = None

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DiagnosticPack:
        return cls.model_validate(data)


class InvestigationResult(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    investigation_id: str = Field(default_factory=lambda: str(uuid4()))
    incident_id: str
    status: InvestigationStatus
    evidence_bundle: EvidenceBundle | None = None
    root_cause: RootCause | None = None
    recovery_recommendation: RecoveryRecommendation | None = None
    diagnostic_pack: DiagnosticPack | None = None
    started_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None
    duration_ms: int = 0
    errors: list[str] = Field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> InvestigationResult:
        return cls.model_validate(data)
