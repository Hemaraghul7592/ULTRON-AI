from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.operations.domain.enums import (
    ComponentType,
    EnvironmentType,
    EventType,
    EvidenceType,
    HealthStatus,
    IncidentSeverity,
    IncidentStatus,
    MetricType,
)
from app.operations.domain.models import (
    ComponentHealth,
    DiagnosticPack,
    EvidenceItem,
    HealthSnapshot,
    Incident,
    MetricSample,
)
from app.operations.domain.value_objects import ConfidenceScore, RiskScore


def _uuid() -> str:
    return str(uuid4())


def _utcnow() -> datetime:
    return datetime.now(UTC)


class UaesHealthSnapshot(Base):
    __tablename__ = "uaes_health_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    environment: Mapped[EnvironmentType] = mapped_column(String(20), nullable=False)
    overall_status: Mapped[HealthStatus] = mapped_column(String(20), nullable=False)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow,
    )
    source: Mapped[str] = mapped_column(String(100), nullable=False)

    components: Mapped[list[UaesHealthComponent]] = relationship(
        back_populates="snapshot",
        cascade="all, delete-orphan",
        order_by="UaesHealthComponent.observed_at",
    )

    def to_domain(self) -> HealthSnapshot:
        return HealthSnapshot(
            snapshot_id=self.id,
            environment=self.environment,
            overall_status=self.overall_status,
            overall_score=self.overall_score,
            collected_at=self.collected_at,
            components=[component.to_domain() for component in self.components],
            source=self.source,
        )

    @classmethod
    def from_domain(cls, snapshot: HealthSnapshot) -> UaesHealthSnapshot:
        entity = cls(
            id=snapshot.snapshot_id,
            environment=snapshot.environment,
            overall_status=snapshot.overall_status,
            overall_score=snapshot.overall_score,
            collected_at=snapshot.collected_at,
            source=snapshot.source,
        )
        entity.components = [
            UaesHealthComponent.from_domain(component, snapshot_id=snapshot.snapshot_id)
            for component in snapshot.components
        ]
        return entity


class UaesHealthComponent(Base):
    __tablename__ = "uaes_health_components"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    snapshot_id: Mapped[str] = mapped_column(
        ForeignKey("uaes_health_snapshots.id", ondelete="CASCADE"), nullable=False,
    )
    component_id: Mapped[str] = mapped_column(String(36), nullable=False)
    component_type: Mapped[ComponentType] = mapped_column(String(30), nullable=False)
    component_name: Mapped[str] = mapped_column(String(100), nullable=False)
    environment: Mapped[EnvironmentType] = mapped_column(String(20), nullable=False)
    status: Mapped[HealthStatus] = mapped_column(String(20), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    message: Mapped[str] = mapped_column(String(500), nullable=False)
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow,
    )
    details_json: Mapped[dict[str, str]] = mapped_column(JSON, nullable=False, default=dict)

    snapshot: Mapped[UaesHealthSnapshot] = relationship(back_populates="components")

    def to_domain(self) -> ComponentHealth:
        return ComponentHealth(
            component_id=self.component_id,
            component_type=self.component_type,
            component_name=self.component_name,
            environment=self.environment,
            status=self.status,
            score=self.score,
            message=self.message,
            observed_at=self.observed_at,
            details=dict(self.details_json),
        )

    @classmethod
    def from_domain(cls, component: ComponentHealth, snapshot_id: str) -> UaesHealthComponent:
        return cls(
            snapshot_id=snapshot_id,
            component_id=component.component_id,
            component_type=component.component_type,
            component_name=component.component_name,
            environment=component.environment,
            status=component.status,
            score=component.score,
            message=component.message,
            observed_at=component.observed_at,
            details_json=dict(component.details),
        )


class UaesIncident(Base):
    __tablename__ = "uaes_incidents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow,
    )
    severity: Mapped[IncidentSeverity] = mapped_column(String(20), nullable=False)
    component: Mapped[ComponentType] = mapped_column(String(30), nullable=False)
    environment: Mapped[EnvironmentType] = mapped_column(String(20), nullable=False)
    summary: Mapped[str] = mapped_column(String(200), nullable=False)
    detailed_description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[IncidentStatus] = mapped_column(
        String(20), nullable=False, default=IncidentStatus.OPEN,
    )
    resolution: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    recovery_plan: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    evidence: Mapped[list[UaesIncidentEvidence]] = relationship(
        back_populates="incident",
        cascade="all, delete-orphan",
        order_by="UaesIncidentEvidence.collected_at",
    )
    diagnostic_packs: Mapped[list[UaesDiagnosticPack]] = relationship(
        back_populates="incident",
        cascade="all, delete-orphan",
        order_by="UaesDiagnosticPack.generated_at",
    )

    __table_args__ = (
        Index("ix_uaes_incidents_status", "status", "timestamp"),
        Index("ix_uaes_incidents_component", "component"),
    )

    def to_domain(self) -> Incident:
        return Incident(
            incident_id=self.id,
            timestamp=self.timestamp,
            severity=self.severity,
            component=self.component,
            environment=self.environment,
            summary=self.summary,
            detailed_description=self.detailed_description,
            evidence=[item.to_domain() for item in self.evidence],
            status=self.status,
            resolution=self.resolution,
            confidence=ConfidenceScore(value=self.confidence),
            recovery_plan=self.recovery_plan,
            duration=None
            if self.duration_seconds is None
            else timedelta(seconds=self.duration_seconds),
            risk=None if self.risk_score is None else RiskScore(value=self.risk_score),
        )

    @classmethod
    def from_domain(cls, incident: Incident) -> UaesIncident:
        entity = cls(
            id=incident.incident_id,
            timestamp=incident.timestamp,
            severity=incident.severity,
            component=incident.component,
            environment=incident.environment,
            summary=incident.summary,
            detailed_description=incident.detailed_description,
            status=incident.status,
            resolution=incident.resolution,
            confidence=incident.confidence.value,
            recovery_plan=incident.recovery_plan,
            duration_seconds=None
            if incident.duration is None
            else incident.duration.total_seconds(),
            risk_score=None if incident.risk is None else incident.risk.value,
        )
        entity.evidence = [
            UaesIncidentEvidence.from_domain(item, incident_id=incident.incident_id)
            for item in incident.evidence
        ]
        return entity


class UaesIncidentEvidence(Base):
    __tablename__ = "uaes_incident_evidence"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    incident_id: Mapped[str] = mapped_column(
        ForeignKey("uaes_incidents.id", ondelete="CASCADE"), nullable=False,
    )
    evidence_type: Mapped[EvidenceType] = mapped_column(String(40), nullable=False)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow,
    )
    payload_ref: Mapped[str] = mapped_column(String(255), nullable=False)
    redacted_excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    checksum: Mapped[str] = mapped_column(String(128), nullable=False)
    metadata_json: Mapped[dict[str, str]] = mapped_column(JSON, nullable=False, default=dict)

    incident: Mapped[UaesIncident] = relationship(back_populates="evidence")

    def to_domain(self) -> EvidenceItem:
        return EvidenceItem(
            evidence_id=self.id,
            incident_id=self.incident_id,
            evidence_type=self.evidence_type,
            source=self.source,
            collected_at=self.collected_at,
            payload_ref=self.payload_ref,
            redacted_excerpt=self.redacted_excerpt,
            checksum=self.checksum,
            metadata=dict(self.metadata_json),
        )

    @classmethod
    def from_domain(cls, evidence: EvidenceItem, incident_id: str) -> UaesIncidentEvidence:
        return cls(
            id=evidence.evidence_id,
            incident_id=incident_id,
            evidence_type=evidence.evidence_type,
            source=evidence.source,
            collected_at=evidence.collected_at,
            payload_ref=evidence.payload_ref,
            redacted_excerpt=evidence.redacted_excerpt,
            checksum=evidence.checksum,
            metadata_json=dict(evidence.metadata),
        )


class UaesMetric(Base):
    __tablename__ = "uaes_metrics"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    metric_type: Mapped[MetricType] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    component: Mapped[ComponentType | None] = mapped_column(String(30), nullable=True)
    environment: Mapped[EnvironmentType] = mapped_column(String(20), nullable=False)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow,
    )
    tags_json: Mapped[dict[str, str]] = mapped_column(JSON, nullable=False, default=dict)
    incident_id: Mapped[str | None] = mapped_column(
        ForeignKey("uaes_incidents.id", ondelete="SET NULL"), nullable=True,
    )

    __table_args__ = (
        Index("ix_uaes_metrics_name", "name", "observed_at"),
        Index("ix_uaes_metrics_type", "metric_type", "observed_at"),
    )

    def to_domain(self) -> MetricSample:
        return MetricSample(
            metric_id=self.id,
            metric_type=self.metric_type,
            name=self.name,
            value=self.value,
            unit=self.unit,
            component=self.component,
            environment=self.environment,
            source=self.source,
            observed_at=self.observed_at,
            tags=dict(self.tags_json),
        )

    @classmethod
    def from_domain(cls, metric: MetricSample, incident_id: str | None = None) -> UaesMetric:
        return cls(
            id=metric.metric_id,
            metric_type=metric.metric_type,
            name=metric.name,
            value=metric.value,
            unit=metric.unit,
            component=metric.component,
            environment=metric.environment,
            source=metric.source,
            observed_at=metric.observed_at,
            tags_json=dict(metric.tags),
            incident_id=incident_id,
        )


class UaesDiagnosticPack(Base):
    __tablename__ = "uaes_diagnostic_packs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    incident_id: Mapped[str] = mapped_column(
        ForeignKey("uaes_incidents.id", ondelete="CASCADE"), nullable=False,
    )
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow,
    )
    summary: Mapped[str] = mapped_column(String(1000), nullable=False)
    log_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    metric_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    config_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    environment_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    commit_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    evidence_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)

    incident: Mapped[UaesIncident] = relationship(back_populates="diagnostic_packs")

    def to_domain(self) -> DiagnosticPack:
        return DiagnosticPack(
            pack_id=self.id,
            incident_id=self.incident_id,
            generated_at=self.generated_at,
            summary=self.summary,
            log_ref=self.log_ref,
            metric_ref=self.metric_ref,
            config_ref=self.config_ref,
            environment_ref=self.environment_ref,
            commit_ref=self.commit_ref,
            evidence=[EvidenceItem.model_validate(item) for item in self.evidence_json],
        )

    @classmethod
    def from_domain(cls, pack: DiagnosticPack) -> UaesDiagnosticPack:
        return cls(
            id=pack.pack_id,
            incident_id=pack.incident_id,
            generated_at=pack.generated_at,
            summary=pack.summary,
            log_ref=pack.log_ref,
            metric_ref=pack.metric_ref,
            config_ref=pack.config_ref,
            environment_ref=pack.environment_ref,
            commit_ref=pack.commit_ref,
            evidence_json=[item.to_dict() for item in pack.evidence],
        )


class UaesEvent(Base):
    __tablename__ = "uaes_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    event_type: Mapped[EventType] = mapped_column(String(50), nullable=False)
    aggregate_type: Mapped[str] = mapped_column(String(100), nullable=False)
    aggregate_id: Mapped[str] = mapped_column(String(36), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow,
    )
    correlation_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    causation_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    source: Mapped[str] = mapped_column(String(100), nullable=False, default="uaes")
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    __table_args__ = (
        Index("ix_uaes_events_aggregate", "aggregate_type", "aggregate_id", "occurred_at"),
        Index("ix_uaes_events_type", "event_type", "occurred_at"),
    )
