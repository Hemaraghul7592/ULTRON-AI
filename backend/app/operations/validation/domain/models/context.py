from __future__ import annotations

from datetime import datetime  # noqa: TC003
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.operations.validation.domain.models.history import PolicyPack  # noqa: TC001
from app.operations.validation.domain.models.request import (  # noqa: TC001
    ValidationEvidence,
    ValidationPolicy,
    ValidationRequest,
)
from app.operations.validation.domain.value_objects import TimeRange  # noqa: TC001


class MonitoringSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    cpu_usage_percent: float = Field(default=0.0, ge=0.0, le=100.0)
    memory_usage_mb: float = Field(default=0.0, ge=0.0)
    disk_usage_gb: float = Field(default=0.0, ge=0.0)
    network_latency_ms: float = Field(default=0.0, ge=0.0)
    active_incidents: list[str] = Field(default_factory=list)


class IncidentDetails(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    incident_id: str = Field(..., min_length=1, max_length=100)
    severity: str = Field(..., min_length=1, max_length=50)
    category: str | None = Field(default=None, min_length=1, max_length=100)
    age_hours: float = Field(default=0.0, ge=0.0)
    description: str = ""


class DependencyGraph(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    nodes: list[str] = Field(default_factory=list)
    edges: list[tuple[str, str]] = Field(default_factory=list)
    affected_components: list[str] = Field(default_factory=list)
    reverse_dependencies: list[str] = Field(default_factory=list)
    critical_path: list[str] = Field(default_factory=list)


class RuntimeSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    active_deployments: list[str] = Field(default_factory=list)
    maintenance_window_active: bool = False
    deployment_in_progress: bool = False


class ExecutionConstraints(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    max_execution_time_seconds: int = Field(default=3600, ge=1, le=86400)
    required_approvals: list[str] = Field(default_factory=list)
    blocked_time_ranges: list[TimeRange] = Field(default_factory=list)


class ValidationContext(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    # ── Request ──────────────────────────────────────────────
    request: ValidationRequest

    # ── Planner Result ───────────────────────────────────────
    planner_result: dict[str, Any]
    planner_strategy: str | None = None
    planner_confidence: float | None = Field(default=None, ge=0.0, le=1.0)

    # ── Monitoring Snapshot ──────────────────────────────────
    monitoring_snapshot: MonitoringSnapshot
    cpu_usage_percent: float = Field(default=0.0, ge=0.0, le=100.0)
    memory_usage_mb: float = Field(default=0.0, ge=0.0)
    disk_usage_gb: float = Field(default=0.0, ge=0.0)
    network_latency_ms: float = Field(default=0.0, ge=0.0)
    active_incidents: list[str] = Field(default_factory=list)

    # ── Incident ─────────────────────────────────────────────
    incident: IncidentDetails | None = None
    incident_severity: str | None = Field(default=None, min_length=1, max_length=50)
    incident_category: str | None = Field(default=None, min_length=1, max_length=100)
    incident_age_hours: float | None = Field(default=None, ge=0.0)

    # ── Dependency Graph ─────────────────────────────────────
    dependency_graph: DependencyGraph
    affected_components: list[str] = Field(default_factory=list)
    reverse_dependencies: list[str] = Field(default_factory=list)
    critical_path: list[str] = Field(default_factory=list)

    # ── Policy Pack ──────────────────────────────────────────
    policy_pack: PolicyPack
    active_policies: list[ValidationPolicy] = Field(default_factory=list)
    enforcement_mode: str = Field(default="hard", min_length=1, max_length=50)

    # ── Runtime Snapshot ─────────────────────────────────────
    runtime_snapshot: RuntimeSnapshot
    active_deployments: list[str] = Field(default_factory=list)
    maintenance_window_active: bool = False
    deployment_in_progress: bool = False

    # ── Collected Evidence ───────────────────────────────────
    collected_evidence: list[ValidationEvidence] = Field(default_factory=list)

    # ── Execution Constraints ────────────────────────────────
    execution_constraints: ExecutionConstraints
    max_execution_time_seconds: int = Field(default=3600, ge=1, le=86400)
    required_approvals: list[str] = Field(default_factory=list)
    blocked_time_ranges: list[TimeRange] = Field(default_factory=list)

    # ── Historical Context ───────────────────────────────────
    historical_failures: int = Field(default=0, ge=0)
    false_positive_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    similar_plan_outcomes: list[str] = Field(default_factory=list)

    # ── Metadata ─────────────────────────────────────────────
    metadata: dict[str, Any] = Field(default_factory=dict)
    built_at: datetime
    built_by: str = Field(default="system", min_length=1, max_length=200)
