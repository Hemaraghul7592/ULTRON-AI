from __future__ import annotations

from datetime import datetime  # noqa: TC003
from typing import Any
from uuid import uuid4

from pydantic import Field

from app.operations.domain.value_objects import DomainModel, utc_now


class PlannerDomainEvent(DomainModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str
    occurred_at: datetime = Field(default_factory=utc_now)
    correlation_id: str | None = None
    source: str = Field(default="uaes-planner", min_length=1, max_length=100)

    def payload(self) -> dict[str, Any]:
        return self.to_dict()


class RepairPlanningStarted(PlannerDomainEvent):
    event_type: str = "repair_planning_started"
    plan_id: str = ""
    incident_id: str = ""


class RepairCandidateGenerated(PlannerDomainEvent):
    event_type: str = "repair_candidate_generated"
    plan_id: str = ""
    candidate_id: str = ""
    strategy_id: str = ""
    repair_type: str = ""


class RepairRiskCalculated(PlannerDomainEvent):
    event_type: str = "repair_risk_calculated"
    plan_id: str = ""
    candidate_id: str = ""
    risk_level: str = ""
    risk_score: float = 0.0


class RepairConfidenceCalculated(PlannerDomainEvent):
    event_type: str = "repair_confidence_calculated"
    plan_id: str = ""
    candidate_id: str = ""
    confidence_dimensions: dict[str, Any] = Field(default_factory=dict)


class RepairPlanApproved(PlannerDomainEvent):
    event_type: str = "repair_plan_approved"
    plan_id: str = ""
    approved_by: str = ""


class RepairPlanRejected(PlannerDomainEvent):
    event_type: str = "repair_plan_rejected"
    plan_id: str = ""
    rejected_by: str = ""
    reason: str = ""


class RepairPlanningCompleted(PlannerDomainEvent):
    event_type: str = "repair_planning_completed"
    plan_id: str = ""
    incident_id: str = ""
    selected_candidate_id: str = ""
    risk_level: str = ""
    confidence_dimensions: dict[str, Any] = Field(default_factory=dict)
    approval_level: str = ""
    planning_duration_ms: int = 0


class RepairSimulated(PlannerDomainEvent):
    event_type: str = "repair_simulated"
    plan_id: str = ""
    simulation_id: str = ""
    overall_outcome: str = ""
    candidate_count: int = 0


class RepairCostEstimated(PlannerDomainEvent):
    event_type: str = "repair_cost_estimated"
    plan_id: str = ""
    candidate_id: str = ""
    operational_cost: float = 0.0
    downtime_seconds: int = 0


class RepairConstraintsChecked(PlannerDomainEvent):
    event_type: str = "repair_constraints_checked"
    plan_id: str = ""
    hard_constraints_total: int = 0
    hard_constraints_satisfied: int = 0
    soft_constraints_total: int = 0
    soft_constraints_satisfied: int = 0


class RepairValidationCompleted(PlannerDomainEvent):
    event_type: str = "repair_validation_completed"
    plan_id: str = ""
    validation_stage: str = ""
    checks_passed: int = 0
    checks_failed: int = 0
    all_passed: bool = False


class RepairKnowledgeConsulted(PlannerDomainEvent):
    event_type: str = "repair_knowledge_consulted"
    plan_id: str = ""
    incident_id: str = ""
    similar_incidents_found: int = 0
    strategies_informed: list[str] = Field(default_factory=list)


class RepairAttempted(PlannerDomainEvent):
    event_type: str = "repair_attempted"
    plan_id: str = ""
    incident_id: str = ""
    strategy_id: str = ""
    risk_level: str = ""
    confidence_score: float = 0.0


class RepairSucceeded(PlannerDomainEvent):
    event_type: str = "repair_succeeded"
    plan_id: str = ""
    duration_seconds: int = 0
    strategy_id: str = ""


class RepairFailed(PlannerDomainEvent):
    event_type: str = "repair_failed"
    plan_id: str = ""
    failure_reason: str = ""
    strategy_id: str = ""


def planner_event_from_dict(data: dict[str, Any]) -> PlannerDomainEvent:
    event_type = data.get("event_type", "")
    event_map: dict[str, type[PlannerDomainEvent]] = {
        "repair_planning_started": RepairPlanningStarted,
        "repair_candidate_generated": RepairCandidateGenerated,
        "repair_risk_calculated": RepairRiskCalculated,
        "repair_confidence_calculated": RepairConfidenceCalculated,
        "repair_plan_approved": RepairPlanApproved,
        "repair_plan_rejected": RepairPlanRejected,
        "repair_planning_completed": RepairPlanningCompleted,
        "repair_simulated": RepairSimulated,
        "repair_cost_estimated": RepairCostEstimated,
        "repair_constraints_checked": RepairConstraintsChecked,
        "repair_validation_completed": RepairValidationCompleted,
        "repair_knowledge_consulted": RepairKnowledgeConsulted,
        "repair_attempted": RepairAttempted,
        "repair_succeeded": RepairSucceeded,
        "repair_failed": RepairFailed,
    }
    event_cls = event_map.get(event_type)
    if event_cls is None:
        return PlannerDomainEvent.model_validate(data)
    return event_cls.model_validate(data)
