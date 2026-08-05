from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.operations.validation.domain.enums import (  # noqa: TC001
    CascadeRisk,
    RollbackComplexity,
)
from app.operations.validation.domain.value_objects import (  # noqa: TC001
    ConfidenceScore,
    RiskScore,
)


class SafetyFactor(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    factor: str = Field(..., min_length=1, max_length=200)
    impact: str = Field(..., min_length=1, max_length=200)
    mitigation: str | None = Field(default=None, min_length=1, max_length=500)


class SafetyAssessment(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    risk_score: RiskScore
    confidence_score: ConfidenceScore
    blast_radius: int = Field(default=0, ge=0)
    historical_failures: int = Field(default=0, ge=0)
    is_catastrophic: bool
    requires_human_approval: bool
    assessment_summary: str = Field(..., min_length=1, max_length=1000)
    factors: list[SafetyFactor] = Field(default_factory=list)


class CompatibilityAssessment(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    config_compatible: bool
    environment_compatible: bool
    version_compatible: bool
    config_conflicts: list[str] = Field(default_factory=list)
    environment_mismatches: list[str] = Field(default_factory=list)
    version_incompatibilities: list[str] = Field(default_factory=list)
    pre_release_components: list[str] = Field(default_factory=list)
    assessment_summary: str = Field(..., min_length=1, max_length=1000)


class RollbackAssessment(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    rollback_available: bool
    automatic_rollback: bool
    rollback_tested: bool
    rollback_success_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    rollback_complexity: RollbackComplexity
    data_loss_risk: bool
    estimated_rollback_time_seconds: int = Field(default=0, ge=0)
    assessment_summary: str = Field(..., min_length=1, max_length=1000)


class SimulationAssessment(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    simulation_performed: bool
    simulation_outcome: str = Field(..., min_length=1, max_length=200)
    preconditions_met: bool
    postconditions_met: bool
    simulation_duration_ms: int = Field(default=0, ge=0)
    simulation_errors: list[str] = Field(default_factory=list)
    assessment_summary: str = Field(..., min_length=1, max_length=1000)


class DependencyAssessment(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    direct_dependencies: list[str] = Field(default_factory=list)
    reverse_dependencies: list[str] = Field(default_factory=list)
    blast_radius: int = Field(default=0, ge=0)
    cascade_risk: CascadeRisk
    critical_path_affected: bool
    cross_boundary_impact: bool
    dependent_service_count: int = Field(default=0, ge=0)
    assessment_summary: str = Field(..., min_length=1, max_length=1000)


class ResourceAssessment(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    cpu_available_percent: float = Field(default=0.0, ge=0.0, le=100.0)
    memory_available_mb: float = Field(default=0.0, ge=0.0)
    disk_available_gb: float = Field(default=0.0, ge=0.0)
    network_impact: str = Field(..., min_length=1, max_length=50)
    resource_sufficient: bool
    estimated_downtime_seconds: int = Field(default=0, ge=0)
    resource_conflicts: list[str] = Field(default_factory=list)
    assessment_summary: str = Field(..., min_length=1, max_length=1000)


class SecurityAssessment(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    auth_valid: bool
    permissions_sufficient: bool
    elevated_permissions_required: bool
    audit_trail_complete: bool
    security_violations: list[str] = Field(default_factory=list)
    required_roles: list[str] = Field(default_factory=list)
    assessment_summary: str = Field(..., min_length=1, max_length=1000)


class CostBreakdown(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    category: str = Field(..., min_length=1, max_length=100)
    amount: float = Field(default=0.0, ge=0.0)
    description: str = ""


class CostAssessment(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    estimated_cost_usd: float = Field(default=0.0, ge=0.0)
    human_effort_hours: float = Field(default=0.0, ge=0.0)
    budget_remaining_usd: float = Field(default=0.0, ge=0.0)
    budget_compliant: bool
    cost_breakdown: list[CostBreakdown] = Field(default_factory=list)
    cost_approval_required: bool
    assessment_summary: str = Field(..., min_length=1, max_length=1000)
