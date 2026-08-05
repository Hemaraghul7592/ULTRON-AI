from __future__ import annotations

from datetime import datetime  # noqa: TC003
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from app.operations.planner.domain.models import (
        CandidateSimulation,
        ConfidenceDimensions,
        RepairArtifact,
        RepairCandidate,
        RepairCost,
        RepairGraph,
        RepairGraphNode,
        RepairPlan,
        RepairRisk,
        SimulationResult,
    )

# --- Graph ---


class RepairGraphNodeResponse(BaseModel):
    node_id: str
    node_type: str
    action: str
    command: str | None = None
    parameters: dict[str, str] = Field(default_factory=dict)
    dependencies: list[str] = Field(default_factory=list)
    timeout_seconds: int = 300
    can_fail: bool = False
    estimated_duration_seconds: int = 0

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_domain(cls, node: RepairGraphNode) -> RepairGraphNodeResponse:
        return cls(
            node_id=node.node_id,
            node_type=node.node_type.value
            if hasattr(node.node_type, "value")
            else str(node.node_type),
            action=node.action,
            command=node.command,
            parameters=dict(node.parameters),
            dependencies=list(node.dependencies),
            timeout_seconds=node.timeout_seconds,
            can_fail=node.can_fail,
            estimated_duration_seconds=node.estimated_duration_seconds,
        )


class RepairGraphResponse(BaseModel):
    graph_id: str
    nodes: list[RepairGraphNodeResponse] = Field(default_factory=list)
    edges: list[tuple[str, str]] = Field(default_factory=list)
    entry_nodes: list[str] = Field(default_factory=list)
    exit_nodes: list[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_domain(cls, graph: RepairGraph) -> RepairGraphResponse:
        return cls(
            graph_id=graph.graph_id,
            nodes=[RepairGraphNodeResponse.from_domain(n) for n in graph.nodes],
            edges=[(s, d) for s, d in graph.edges],
            entry_nodes=list(graph.entry_nodes),
            exit_nodes=list(graph.exit_nodes),
        )


# --- Risk ---


class RepairRiskResponse(BaseModel):
    score: float
    level: str
    factors: list[str] = Field(default_factory=list)
    mitigations: list[str] = Field(default_factory=list)
    requires_backup: bool = False
    requires_maintenance_window: bool = False
    downtime_estimate_seconds: int = 0

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_domain(cls, risk: RepairRisk) -> RepairRiskResponse:
        return cls(
            score=risk.score,
            level=risk.level.value if hasattr(risk.level, "value") else str(risk.level),
            factors=list(risk.factors),
            mitigations=list(risk.mitigations),
            requires_backup=risk.requires_backup,
            requires_maintenance_window=risk.requires_maintenance_window,
            downtime_estimate_seconds=risk.downtime_estimate_seconds,
        )


# --- Confidence ---


class ConfidenceDimensionsResponse(BaseModel):
    evidence_confidence: float = 0.0
    root_cause_confidence: float = 0.0
    repair_confidence: float = 0.0
    validation_confidence: float = 0.0
    overall_score: float = 0.0
    dimension_scores: dict[str, float] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_domain(cls, dim: ConfidenceDimensions) -> ConfidenceDimensionsResponse:
        return cls(
            evidence_confidence=dim.evidence_confidence,
            root_cause_confidence=dim.root_cause_confidence,
            repair_confidence=dim.repair_confidence,
            validation_confidence=dim.validation_confidence,
            overall_score=dim.overall_score,
            dimension_scores=dict(dim.dimension_scores),
        )


# --- Cost ---


class RepairCostResponse(BaseModel):
    execution_time_seconds: int = 0
    cpu_impact_percent: float = 0.0
    memory_impact_mb: float = 0.0
    operational_cost: float = 0.0
    human_effort_hours: float = 0.0
    requires_downtime: bool = False
    downtime_seconds: int = 0

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_domain(cls, cost: RepairCost) -> RepairCostResponse:
        return cls(
            execution_time_seconds=cost.execution_time_seconds,
            cpu_impact_percent=cost.cpu_impact_percent,
            memory_impact_mb=cost.memory_impact_mb,
            operational_cost=cost.operational_cost,
            human_effort_hours=cost.human_effort_hours,
            requires_downtime=cost.requires_downtime,
            downtime_seconds=cost.downtime_seconds,
        )


# --- Simulation ---


class CandidateSimulationResponse(BaseModel):
    simulation_id: str
    candidate_id: str
    outcome: str
    expected_risk_change: float = 0.0
    preconditions_met: bool = False
    postconditions_met: bool = False
    simulated_duration_seconds: int = 0
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_domain(cls, sim: CandidateSimulation) -> CandidateSimulationResponse:
        return cls(
            simulation_id=sim.simulation_id,
            candidate_id=sim.candidate_id,
            outcome=sim.outcome.value if hasattr(sim.outcome, "value") else str(sim.outcome),
            expected_risk_change=sim.expected_risk_change,
            preconditions_met=sim.preconditions_met,
            postconditions_met=sim.postconditions_met,
            simulated_duration_seconds=sim.simulated_duration_seconds,
            warnings=list(sim.warnings),
            errors=list(sim.errors),
        )


class SimulationResultResponse(BaseModel):
    result_id: str
    plan_id: str
    recommended_candidate_id: str | None = None
    overall_outcome: str = "unknown"
    candidate_count: int = 0
    simulation_duration_ms: int = 0

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_domain(cls, result: SimulationResult) -> SimulationResultResponse:
        return cls(
            result_id=result.result_id,
            plan_id=result.plan_id,
            recommended_candidate_id=result.recommended_candidate_id,
            overall_outcome=result.overall_outcome.value
            if hasattr(result.overall_outcome, "value")
            else str(result.overall_outcome),
            candidate_count=len(result.candidate_simulations),
            simulation_duration_ms=result.simulation_duration_ms,
        )


# --- Candidate ---


class RepairCandidateResponse(BaseModel):
    candidate_id: str
    repair_type: str
    strategy_name: str
    description: str
    repair_graph: RepairGraphResponse | None = None
    risk: RepairRiskResponse | None = None
    confidence: ConfidenceDimensionsResponse | None = None
    cost: RepairCostResponse | None = None
    estimated_duration_seconds: int = 0
    score: float = 0.0
    rank: int = 0
    simulation: CandidateSimulationResponse | None = None

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_domain(cls, c: RepairCandidate) -> RepairCandidateResponse:
        return cls(
            candidate_id=c.candidate_id,
            repair_type=c.repair_type.value
            if hasattr(c.repair_type, "value")
            else str(c.repair_type),
            strategy_name=c.strategy_name,
            description=c.description,
            repair_graph=RepairGraphResponse.from_domain(c.repair_graph)
            if c.repair_graph
            else None,
            risk=RepairRiskResponse.from_domain(c.risk) if c.risk else None,
            confidence=ConfidenceDimensionsResponse.from_domain(c.confidence)
            if c.confidence
            else None,
            cost=RepairCostResponse.from_domain(c.cost) if c.cost else None,
            estimated_duration_seconds=c.estimated_duration_seconds,
            score=c.score,
            rank=c.rank,
            simulation=CandidateSimulationResponse.from_domain(c.simulation)
            if c.simulation
            else None,
        )


# --- Plan ---


class RepairPlanResponse(BaseModel):
    plan_id: str
    incident_id: str
    status: str
    created_at: datetime
    updated_at: datetime
    planning_duration_ms: int = 0
    total_candidates_evaluated: int = 0
    strategy_used: str = ""
    environment: str = ""
    component_type: str = ""
    component_name: str = ""
    selected_candidate_id: str | None = None

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_domain(cls, plan: RepairPlan) -> RepairPlanResponse:
        return cls(
            plan_id=plan.plan_id,
            incident_id=plan.incident_id,
            status=plan.status.value if hasattr(plan.status, "value") else str(plan.status),
            created_at=plan.created_at,
            updated_at=plan.updated_at,
            planning_duration_ms=plan.planning_duration_ms,
            total_candidates_evaluated=plan.total_candidates_evaluated,
            strategy_used=plan.strategy_used,
            environment=plan.environment,
            component_type=plan.component_type,
            component_name=plan.component_name,
            selected_candidate_id=(
                plan.selected_candidate.candidate_id if plan.selected_candidate else None
            ),
        )


class PlanListResponse(BaseModel):
    plans: list[RepairPlanResponse] = Field(default_factory=list)
    count: int = 0


class PlanDetailResponse(BaseModel):
    plan: RepairPlanResponse
    candidates: list[RepairCandidateResponse] = Field(default_factory=list)
    simulation: SimulationResultResponse | None = None


class StrategySummaryResponse(BaseModel):
    id: str
    name: str
    repair_type: str
    root_cause_categories: list[str] = Field(default_factory=list)
    estimated_duration_seconds: int = 0


class StrategyListResponse(BaseModel):
    strategies: list[StrategySummaryResponse] = Field(default_factory=list)
    count: int = 0


class RepairArtifactResponse(BaseModel):
    artifact_id: str
    plan_id: str
    incident_id: str
    executed_at: datetime
    completed_at: datetime | None = None
    success: bool = False
    steps_completed: int = 0
    steps_total: int = 0
    duration_seconds: int = 0

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_domain(cls, a: RepairArtifact) -> RepairArtifactResponse:
        return cls(
            artifact_id=a.artifact_id,
            plan_id=a.plan_id,
            incident_id=a.incident_id,
            executed_at=a.executed_at,
            completed_at=a.completed_at,
            success=a.success,
            steps_completed=a.steps_completed,
            steps_total=a.steps_total,
            duration_seconds=a.duration_seconds,
        )


class HistoryResponse(BaseModel):
    artifacts: list[RepairArtifactResponse] = Field(default_factory=list)
    count: int = 0


class GeneratePlanRequest(BaseModel):
    incident_id: str = Field(..., min_length=1, max_length=36)


class ApprovePlanRequest(BaseModel):
    approved_by: str = Field(..., min_length=1, max_length=100)
    justification: str = Field(default="", max_length=2000)


class RejectPlanRequest(BaseModel):
    rejected_by: str = Field(..., min_length=1, max_length=100)
    reason: str = Field(..., min_length=1, max_length=2000)


class CancelPlanRequest(BaseModel):
    cancelled_by: str = Field(..., min_length=1, max_length=100)
    reason: str = Field(default="", max_length=2000)
