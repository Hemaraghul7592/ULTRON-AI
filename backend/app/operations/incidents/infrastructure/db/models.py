from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.operations.domain.value_objects import ConfidenceScore, RiskScore
from app.operations.incidents.domain.enums import IncidentStatus
from app.operations.incidents.domain.models import (
    DiagnosticPack,
    Incident,
    IncidentEvidence,
    RootCause,
)


def _uuid() -> str:
    return str(uuid4())


def _utcnow() -> datetime:
    return datetime.now(UTC)


class UaesIncidentV3(Base):
    __tablename__ = "uaes_incidents_v3"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    component_type: Mapped[str] = mapped_column(String(30), nullable=False)
    component_name: Mapped[str] = mapped_column(String(100), nullable=False)
    environment: Mapped[str] = mapped_column(String(20), nullable=False)
    summary: Mapped[str] = mapped_column(String(200), nullable=False)
    detailed_description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default=IncidentStatus.DETECTED.value
    )
    triggered_by_event: Mapped[str | None] = mapped_column(String(100), nullable=True)
    triggered_by_component: Mapped[str | None] = mapped_column(String(100), nullable=True)
    triggered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    resolution: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    recovery_recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    tags_json: Mapped[dict[str, str]] = mapped_column(JSON, nullable=False, default=dict)

    evidence: Mapped[list[UaesIncidentEvidenceV3]] = relationship(
        back_populates="incident",
        cascade="all, delete-orphan",
        order_by="UaesIncidentEvidenceV3.collected_at",
    )
    root_causes: Mapped[list[UaesRootCause]] = relationship(
        back_populates="incident",
        cascade="all, delete-orphan",
        order_by="UaesRootCause.determined_at",
    )
    diagnostic_packs: Mapped[list[UaesDiagnosticPackV3]] = relationship(
        back_populates="incident",
        cascade="all, delete-orphan",
        order_by="UaesDiagnosticPackV3.generated_at",
    )

    __table_args__ = (
        Index("ix_uaes_incidents_v3_status", "status", "timestamp"),
        Index("ix_uaes_incidents_v3_component", "component_type", "component_name"),
    )

    def to_domain(self) -> Incident:
        return Incident(
            incident_id=self.id,
            timestamp=self.timestamp,
            severity=self.severity,
            component_type=self.component_type,
            component_name=self.component_name,
            environment=self.environment,
            summary=self.summary,
            detailed_description=self.detailed_description,
            status=self.status,
            triggered_by_event=self.triggered_by_event,
            triggered_by_component=self.triggered_by_component,
            triggered_at=self.triggered_at,
            resolution=self.resolution,
            confidence=ConfidenceScore(value=self.confidence),
            recovery_recommendation=self.recovery_recommendation,
            duration=None
            if self.duration_seconds is None
            else timedelta(seconds=self.duration_seconds),
            risk=None if self.risk_score is None else RiskScore(value=self.risk_score),
            tags=dict(self.tags_json),
        )

    @classmethod
    def from_domain(cls, incident: Incident) -> UaesIncidentV3:
        return cls(
            id=incident.incident_id,
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
            duration_seconds=None
            if incident.duration is None
            else incident.duration.total_seconds(),
            risk_score=None if incident.risk is None else incident.risk.value,
            tags_json=dict(incident.tags),
        )


class UaesIncidentEvidenceV3(Base):
    __tablename__ = "uaes_incident_evidence_v3"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    incident_id: Mapped[str] = mapped_column(
        ForeignKey("uaes_incidents_v3.id", ondelete="CASCADE"),
        nullable=False,
    )
    category: Mapped[str] = mapped_column(String(40), nullable=False)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    payload_ref: Mapped[str] = mapped_column(String(255), nullable=False)
    redacted_excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    checksum: Mapped[str] = mapped_column(String(128), nullable=False)
    metadata_json: Mapped[dict[str, str]] = mapped_column(JSON, nullable=False, default=dict)

    incident: Mapped[UaesIncidentV3] = relationship(back_populates="evidence")

    __table_args__ = (Index("ix_uaes_incident_evidence_v3_incident", "incident_id"),)

    def to_domain(self) -> IncidentEvidence:
        return IncidentEvidence(
            evidence_id=self.id,
            incident_id=self.incident_id,
            category=self.category,
            source=self.source,
            collected_at=self.collected_at,
            payload_ref=self.payload_ref,
            redacted_excerpt=self.redacted_excerpt,
            checksum=self.checksum,
            metadata=dict(self.metadata_json),
        )

    @classmethod
    def from_domain(
        cls, evidence: IncidentEvidence, incident_id: str
    ) -> UaesIncidentEvidenceV3:
        return cls(
            id=evidence.evidence_id,
            incident_id=incident_id,
            category=evidence.category,
            source=evidence.source,
            collected_at=evidence.collected_at,
            payload_ref=evidence.payload_ref,
            redacted_excerpt=evidence.redacted_excerpt,
            checksum=evidence.checksum,
            metadata_json=dict(evidence.metadata),
        )


class UaesRootCause(Base):
    __tablename__ = "uaes_root_causes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    incident_id: Mapped[str] = mapped_column(
        ForeignKey("uaes_incidents_v3.id", ondelete="CASCADE"),
        nullable=False,
    )
    category: Mapped[str] = mapped_column(String(40), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    supporting_evidence_json: Mapped[list[str]] = mapped_column(
        JSON, nullable=False, default=list
    )
    rule_matched: Mapped[str] = mapped_column(String(200), nullable=False)
    determined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )

    incident: Mapped[UaesIncidentV3] = relationship(back_populates="root_causes")

    __table_args__ = (Index("ix_uaes_root_causes_incident", "incident_id"),)

    def to_domain(self) -> RootCause:
        return RootCause(
            root_cause_id=self.id,
            incident_id=self.incident_id,
            category=self.category,
            description=self.description,
            confidence=ConfidenceScore(value=self.confidence),
            supporting_evidence=list(self.supporting_evidence_json),
            rule_matched=self.rule_matched,
            determined_at=self.determined_at,
        )

    @classmethod
    def from_domain(cls, root_cause: RootCause, incident_id: str) -> UaesRootCause:
        return cls(
            id=root_cause.root_cause_id,
            incident_id=incident_id,
            category=root_cause.category,
            description=root_cause.description,
            confidence=root_cause.confidence.value,
            supporting_evidence_json=list(root_cause.supporting_evidence),
            rule_matched=root_cause.rule_matched,
            determined_at=root_cause.determined_at,
        )


class UaesDiagnosticPackV3(Base):
    __tablename__ = "uaes_diagnostic_packs_v3"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    incident_id: Mapped[str] = mapped_column(
        ForeignKey("uaes_incidents_v3.id", ondelete="CASCADE"),
        nullable=False,
    )
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    summary: Mapped[str] = mapped_column(String(1000), nullable=False)
    pack_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

    incident: Mapped[UaesIncidentV3] = relationship(back_populates="diagnostic_packs")

    __table_args__ = (Index("ix_uaes_diagnostic_packs_v3_incident", "incident_id"),)

    def to_domain(self) -> DiagnosticPack:
        return DiagnosticPack.model_validate(self.pack_json)

    @classmethod
    def from_domain(cls, pack: DiagnosticPack, incident_id: str) -> UaesDiagnosticPackV3:
        return cls(
            id=pack.pack_id,
            incident_id=incident_id,
            generated_at=pack.generated_at,
            summary=pack.summary,
            pack_json=pack.to_dict(),
        )
