from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _uuid() -> str:
    return str(uuid4())


def _utcnow() -> datetime:
    return datetime.now(UTC)


class UaesRepairPlan(Base):
    __tablename__ = "uaes_repair_plans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    incident_id: Mapped[str] = mapped_column(String(36), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="draft")
    selected_candidate_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    environment: Mapped[str] = mapped_column(String(20), nullable=False)
    component_type: Mapped[str] = mapped_column(String(30), nullable=False)
    component_name: Mapped[str] = mapped_column(String(100), nullable=False)
    strategy_used: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    planning_duration_ms: Mapped[int] = mapped_column(nullable=False, default=0)
    total_candidates_evaluated: Mapped[int] = mapped_column(nullable=False, default=0)
    knowledge_consulted: Mapped[bool] = mapped_column(nullable=False, default=False)
    knowledge_snapshot_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    plan_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    constraints_json: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, nullable=False, default=list
    )
    approval_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    execution_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    simulation_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    validation_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    candidates: Mapped[list[UaesRepairCandidate]] = relationship(
        back_populates="plan",
        cascade="all, delete-orphan",
        order_by="UaesRepairCandidate.rank",
    )
    artifacts: Mapped[list[UaesRepairArtifact]] = relationship(
        back_populates="plan",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_uaes_repair_plans_incident", "incident_id"),
        Index("ix_uaes_repair_plans_status", "status", "created_at"),
        Index("ix_uaes_repair_plans_env", "environment", "status"),
    )


class UaesRepairCandidate(Base):
    __tablename__ = "uaes_repair_candidates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    plan_id: Mapped[str] = mapped_column(
        ForeignKey("uaes_repair_plans.id", ondelete="CASCADE"),
        nullable=False,
    )
    repair_type: Mapped[str] = mapped_column(String(40), nullable=False)
    strategy_id: Mapped[str] = mapped_column(String(50), nullable=False)
    strategy_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    rank: Mapped[int] = mapped_column(nullable=False, default=0)
    estimated_duration_seconds: Mapped[int] = mapped_column(nullable=False, default=0)
    risk_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    confidence_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    cost_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    constraints_json: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, nullable=False, default=list
    )
    steps_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    repair_graph_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    simulation_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    prerequisites_json: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    affected_components_json: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    plan: Mapped[UaesRepairPlan] = relationship(back_populates="candidates")

    __table_args__ = (
        Index("ix_uaes_repair_candidates_plan", "plan_id"),
        Index("ix_uaes_repair_candidates_plan_rank", "plan_id", "rank"),
    )


class UaesRepairArtifact(Base):
    __tablename__ = "uaes_repair_artifacts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    plan_id: Mapped[str] = mapped_column(
        ForeignKey("uaes_repair_plans.id", ondelete="CASCADE"),
        nullable=False,
    )
    incident_id: Mapped[str] = mapped_column(String(36), nullable=False)
    executed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    success: Mapped[bool] = mapped_column(nullable=False, default=False)
    steps_completed: Mapped[int] = mapped_column(nullable=False, default=0)
    steps_total: Mapped[int] = mapped_column(nullable=False, default=0)
    output: Mapped[str] = mapped_column(Text, nullable=False, default="")
    errors_json: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    rollback_performed: Mapped[bool] = mapped_column(nullable=False, default=False)
    duration_seconds: Mapped[int] = mapped_column(nullable=False, default=0)

    plan: Mapped[UaesRepairPlan] = relationship(back_populates="artifacts")

    __table_args__ = (
        Index("ix_uaes_repair_artifacts_plan", "plan_id"),
        Index("ix_uaes_repair_artifacts_incident", "incident_id"),
        Index("ix_uaes_repair_artifacts_executed", "executed_at"),
    )


class UaesKnowledgeSnapshot(Base):
    __tablename__ = "uaes_knowledge_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    incident_id: Mapped[str] = mapped_column(String(36), nullable=False)
    root_cause_category: Mapped[str] = mapped_column(String(40), nullable=False)
    component_type: Mapped[str] = mapped_column(String(30), nullable=False)
    environment: Mapped[str] = mapped_column(String(20), nullable=False)
    similar_incidents_json: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, nullable=False, default=list
    )
    success_rates_json: Mapped[dict[str, float]] = mapped_column(JSON, nullable=False, default=dict)
    avg_durations_json: Mapped[dict[str, int]] = mapped_column(JSON, nullable=False, default=dict)
    consulted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )

    __table_args__ = (
        Index("ix_uaes_knowledge_category", "root_cause_category", "component_type"),
        Index("ix_uaes_knowledge_consulted", "consulted_at"),
    )


class UaesLearningEvent(Base):
    __tablename__ = "uaes_learning_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    plan_id: Mapped[str] = mapped_column(String(36), nullable=False)
    incident_id: Mapped[str] = mapped_column(String(36), nullable=False)
    strategy_id: Mapped[str] = mapped_column(String(50), nullable=False)
    root_cause_category: Mapped[str] = mapped_column(String(40), nullable=False)
    success: Mapped[bool] = mapped_column(nullable=False, default=False)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    duration_seconds: Mapped[int] = mapped_column(nullable=False, default=0)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    metadata_json: Mapped[dict[str, str]] = mapped_column(JSON, nullable=False, default=dict)

    __table_args__ = (
        Index("ix_uaes_learning_strategy", "strategy_id", "occurred_at"),
        Index("ix_uaes_learning_category", "root_cause_category", "occurred_at"),
        Index("ix_uaes_learning_plan", "plan_id"),
    )
