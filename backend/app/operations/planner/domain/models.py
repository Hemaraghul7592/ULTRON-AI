from __future__ import annotations

from datetime import datetime  # noqa: TC003
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from app.operations.domain.value_objects import utc_now
from app.operations.planner.domain.enums import (
    ApprovalLevel,
    ConstraintType,
    ExecutionMode,
    RepairGraphNodeType,
    RepairSource,
    RepairStatus,
    RepairType,
    RiskLevel,
    SimulationOutcome,
    ValidationStage,
)

# --- Graph Model ---


class RepairGraphNode(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    node_id: str = Field(default_factory=lambda: str(uuid4()))
    node_type: RepairGraphNodeType
    action: str = Field(..., min_length=1, max_length=500)
    command: str | None = None
    parameters: dict[str, str] = Field(default_factory=dict)
    dependencies: list[str] = Field(default_factory=list)
    timeout_seconds: int = 300
    can_fail: bool = False
    rollback_command: str | None = None
    validation_command: str | None = None
    estimated_duration_seconds: int = 0
    metadata: dict[str, str] = Field(default_factory=dict)


class RepairGraph(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    graph_id: str = Field(default_factory=lambda: str(uuid4()))
    nodes: list[RepairGraphNode] = Field(default_factory=list)
    edges: list[tuple[str, str]] = Field(default_factory=list)
    entry_nodes: list[str] = Field(default_factory=list)
    exit_nodes: list[str] = Field(default_factory=list)

    def topological_order(self) -> list[str]:
        in_degree: dict[str, int] = {n.node_id: 0 for n in self.nodes}
        dependents: dict[str, list[str]] = {n.node_id: [] for n in self.nodes}
        for src, dst in self.edges:
            in_degree[dst] = in_degree.get(dst, 0) + 1
            dependents[src].append(dst)
        queue = sorted([nid for nid, deg in in_degree.items() if deg == 0])
        result: list[str] = []
        while queue:
            node = queue.pop(0)
            result.append(node)
            for dep in sorted(dependents[node]):
                in_degree[dep] -= 1
                if in_degree[dep] == 0:
                    queue.append(dep)
        return result

    def parallel_groups(self) -> list[list[str]]:
        in_degree: dict[str, int] = {n.node_id: 0 for n in self.nodes}
        for _src, dst in self.edges:
            in_degree[dst] += 1
        remaining = {n.node_id for n in self.nodes}
        groups: list[list[str]] = []
        while remaining:
            ready = sorted([nid for nid in remaining if in_degree[nid] == 0])
            groups.append(ready)
            for nid in ready:
                remaining.remove(nid)
                for src, dst in self.edges:
                    if src == nid:
                        in_degree[dst] -= 1
        return groups

    def validate_acyclic(self) -> bool:
        return len(self.topological_order()) == len(self.nodes)


# --- Constraint Model ---


class RepairConstraint(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    constraint_id: str = Field(default_factory=lambda: str(uuid4()))
    constraint_type: ConstraintType
    description: str = Field(..., max_length=500)
    parameters: dict[str, str] = Field(default_factory=dict)
    severity: str = "hard"
    created_by: str = "system"


# --- Cost Model ---


class RepairCost(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    cost_id: str = Field(default_factory=lambda: str(uuid4()))
    execution_time_seconds: int = 0
    cpu_impact_percent: float = 0.0
    memory_impact_mb: float = 0.0
    storage_impact_mb: float = 0.0
    network_impact: str = "none"
    operational_cost: float = 0.0
    human_effort_hours: float = 0.0
    requires_downtime: bool = False
    downtime_seconds: int = 0
    description: str = ""


# --- Confidence Dimensions ---


class ConfidenceDimensions(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    dimensions_id: str = Field(default_factory=lambda: str(uuid4()))
    evidence_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    root_cause_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    repair_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    validation_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence_factors: list[str] = Field(default_factory=list)
    root_cause_factors: list[str] = Field(default_factory=list)
    repair_factors: list[str] = Field(default_factory=list)
    validation_factors: list[str] = Field(default_factory=list)
    overall_score: float = Field(default=0.0, ge=0.0, le=1.0)
    dimension_scores: dict[str, float] = Field(default_factory=dict)

    def compute_overall(
        self,
        w_evidence: float = 0.25,
        w_root_cause: float = 0.30,
        w_repair: float = 0.30,
        w_validation: float = 0.15,
    ) -> float:
        return round(
            w_evidence * self.evidence_confidence
            + w_root_cause * self.root_cause_confidence
            + w_repair * self.repair_confidence
            + w_validation * self.validation_confidence,
            4,
        )


# --- Risk Model ---


class RepairRisk(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    risk_id: str = Field(default_factory=lambda: str(uuid4()))
    score: float = Field(..., ge=0.0, le=100.0)
    level: RiskLevel
    factors: list[str] = Field(default_factory=list)
    mitigations: list[str] = Field(default_factory=list)
    blast_radius: list[str] = Field(default_factory=list)
    requires_backup: bool = False
    requires_maintenance_window: bool = False
    downtime_estimate_seconds: int = 0
    simulation_adjusted: bool = False
    simulation_risk_delta: float = 0.0


# --- Simulation Model ---


class CandidateSimulation(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    simulation_id: str = Field(default_factory=lambda: str(uuid4()))
    candidate_id: str
    plan_id: str
    outcome: SimulationOutcome
    expected_risk_change: float = 0.0
    expected_confidence_change: float = 0.0
    preconditions_met: bool = False
    postconditions_met: bool = False
    simulated_duration_seconds: int = 0
    simulated_resource_impact: dict[str, float] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    simulated_at: datetime = Field(default_factory=utc_now)


class SimulationResult(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    result_id: str = Field(default_factory=lambda: str(uuid4()))
    plan_id: str
    candidate_simulations: list[CandidateSimulation] = Field(default_factory=list)
    recommended_candidate_id: str | None = None
    simulation_duration_ms: int = 0
    overall_outcome: SimulationOutcome = SimulationOutcome.UNKNOWN


# --- Validation Model ---


class ValidationCheck(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    check_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    check_type: str
    command: str | None = None
    expected_value: str | None = None
    component: str | None = None
    timeout_seconds: int = 60
    stage: ValidationStage = ValidationStage.POST_EXECUTION


class ValidationPipelineResult(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    result_id: str = Field(default_factory=lambda: str(uuid4()))
    plan_id: str
    checks: list[ValidationCheck] = Field(default_factory=list)
    passed: list[str] = Field(default_factory=list)
    failed: list[str] = Field(default_factory=list)
    skipped: list[str] = Field(default_factory=list)
    all_passed: bool = False
    validated_at: datetime = Field(default_factory=utc_now)
    validation_duration_ms: int = 0


class RollbackReadinessCheck(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    check_id: str = Field(default_factory=lambda: str(uuid4()))
    plan_id: str
    rollback_available: bool = False
    rollback_automatic: bool = False
    rollback_steps_validated: int = 0
    rollback_steps_total: int = 0
    estimated_rollback_duration_seconds: int = 0
    issues: list[str] = Field(default_factory=list)


# --- Rollback Model ---


class RollbackPlan(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    rollback_id: str = Field(default_factory=lambda: str(uuid4()))
    plan_id: str
    graph: RepairGraph | None = None
    steps: list[RepairGraphNode] = Field(default_factory=list)
    estimated_duration_seconds: int = 0
    automatic: bool = True
    requires_manual_intervention: bool = False
    description: str = Field(..., max_length=2000)
    readiness: RollbackReadinessCheck | None = None


# --- Approval Model ---


class ApprovalStage(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    stage_id: str = Field(default_factory=lambda: str(uuid4()))
    level: ApprovalLevel
    required_by: list[str] = Field(default_factory=list)
    approved_by: str | None = None
    approved_at: datetime | None = None
    rejected_by: str | None = None
    rejected_at: datetime | None = None
    rejection_reason: str | None = None
    timeout_hours: int = 24
    escalation_level: ApprovalLevel | None = None
    status: str = "pending"


class ApprovalRequirement(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    approval_id: str = Field(default_factory=lambda: str(uuid4()))
    plan_id: str
    stages: list[ApprovalStage] = Field(default_factory=list)
    current_stage_index: int = 0
    final_level: ApprovalLevel
    requested_at: datetime = Field(default_factory=utc_now)
    completed: bool = False
    approved: bool = False


# --- Knowledge Model ---


class SimilarIncident(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    incident_id: str
    root_cause_category: str
    strategy_used: str
    success: bool
    risk_level: str
    duration_seconds: int
    similarity_score: float = Field(ge=0.0, le=1.0)


class KnowledgeSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    snapshot_id: str = Field(default_factory=lambda: str(uuid4()))
    incident_id: str
    root_cause_category: str
    similar_incidents: list[SimilarIncident] = Field(default_factory=list)
    historical_success_rates: dict[str, float] = Field(default_factory=dict)
    historical_avg_duration: dict[str, int] = Field(default_factory=dict)
    historical_risk_distribution: dict[str, str] = Field(default_factory=dict)
    consulted_at: datetime = Field(default_factory=utc_now)


# --- Repair Step (legacy, kept for compat) ---


class RepairStep(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    step_id: str = Field(default_factory=lambda: str(uuid4()))
    order: int
    action: str = Field(..., min_length=1, max_length=500)
    command: str | None = None
    parameters: dict[str, str] = Field(default_factory=dict)
    estimated_duration_seconds: int = 0
    rollback_command: str | None = None
    validation_command: str | None = None
    can_fail: bool = False
    timeout_seconds: int = 300


# --- Repair Candidate ---


class RepairCandidate(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    candidate_id: str = Field(default_factory=lambda: str(uuid4()))
    plan_id: str
    repair_type: RepairType
    strategy_id: str
    strategy_name: str
    description: str = Field(..., min_length=1, max_length=2000)
    repair_graph: RepairGraph | None = None
    steps: list[RepairStep] = Field(default_factory=list)
    risk: RepairRisk | None = None
    confidence: ConfidenceDimensions | None = None
    cost: RepairCost | None = None
    constraints: list[RepairConstraint] = Field(default_factory=list)
    estimated_duration_seconds: int = 0
    prerequisites: list[str] = Field(default_factory=list)
    affected_components: list[str] = Field(default_factory=list)
    source: RepairSource = "rule_based"
    score: float = 0.0
    rank: int = 0
    simulation: CandidateSimulation | None = None


# --- Execution Plan ---


class ExecutionPlan(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    plan_id: str
    repair_graph: RepairGraph | None = None
    steps: list[RepairStep] = Field(default_factory=list)
    rollback: RollbackPlan | None = None
    validation: ValidationPipelineResult | None = None
    execution_mode: ExecutionMode = "immediate"
    scheduled_at: datetime | None = None
    timeout_seconds: int = 3600
    constraints: list[RepairConstraint] = Field(default_factory=list)
    cost: RepairCost | None = None


# --- Repair Plan ---


class RepairPlan(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    plan_id: str = Field(default_factory=lambda: str(uuid4()))
    incident_id: str
    status: RepairStatus = RepairStatus.DRAFT
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    expires_at: datetime | None = None
    selected_candidate: RepairCandidate | None = None
    candidates: list[RepairCandidate] = Field(default_factory=list)
    constraints: list[RepairConstraint] = Field(default_factory=list)
    approval: ApprovalRequirement | None = None
    execution_plan: ExecutionPlan | None = None
    rollback_plan: RollbackPlan | None = None
    validation: ValidationPipelineResult | None = None
    simulation_result: SimulationResult | None = None
    planning_duration_ms: int = 0
    total_candidates_evaluated: int = 0
    strategy_used: str = ""
    environment: str = ""
    component_type: str = ""
    component_name: str = ""
    knowledge_consulted: bool = False
    knowledge_snapshot_id: str | None = None


# --- Artifact ---


class RepairArtifact(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    artifact_id: str = Field(default_factory=lambda: str(uuid4()))
    plan_id: str
    incident_id: str
    executed_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None
    success: bool = False
    steps_completed: int = 0
    steps_total: int = 0
    output: str = ""
    errors: list[str] = Field(default_factory=list)
    rollback_performed: bool = False
    duration_seconds: int = 0


# --- Decision ---


class RepairDecision(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    decision_id: str = Field(default_factory=lambda: str(uuid4()))
    plan_id: str
    incident_id: str
    selected_candidate_id: str
    risk_level: RiskLevel
    confidence_dimensions: ConfidenceDimensions | None = None
    approval_level: ApprovalLevel
    approved: bool = False
    executed: bool = False
    artifact: RepairArtifact | None = None
    decided_at: datetime = Field(default_factory=utc_now)


# --- Learning Event ---


class RepairLearningEvent(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str
    plan_id: str
    incident_id: str
    strategy_id: str
    root_cause_category: str
    success: bool
    risk_level: str
    confidence_score: float
    duration_seconds: int
    occurred_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, str] = Field(default_factory=dict)
