from app.operations.planner.domain.events import (
    PlannerDomainEvent,
    RepairAttempted,
    RepairCandidateGenerated,
    RepairConfidenceCalculated,
    RepairConstraintsChecked,
    RepairCostEstimated,
    RepairFailed,
    RepairKnowledgeConsulted,
    RepairPlanApproved,
    RepairPlanningCompleted,
    RepairPlanningStarted,
    RepairPlanRejected,
    RepairRiskCalculated,
    RepairSimulated,
    RepairSucceeded,
    RepairValidationCompleted,
    planner_event_from_dict,
)


class TestPlannerDomainEvent:
    def test_create(self):
        e = PlannerDomainEvent(event_type="test")
        assert e.event_type == "test"
        assert e.source == "uaes-planner"
        assert e.event_id  # auto-generated UUID

    def test_payload(self):
        e = PlannerDomainEvent(event_type="test", correlation_id="corr-1")
        p = e.payload()
        assert p["event_type"] == "test"
        assert p["correlation_id"] == "corr-1"


class TestRepairPlanningStarted:
    def test_create(self):
        e = RepairPlanningStarted(plan_id="p1", incident_id="i1")
        assert e.event_type == "repair_planning_started"
        assert e.plan_id == "p1"


class TestRepairCandidateGenerated:
    def test_create(self):
        e = RepairCandidateGenerated(plan_id="p1", candidate_id="c1", strategy_id="S01")
        assert e.event_type == "repair_candidate_generated"


class TestRepairRiskCalculated:
    def test_create(self):
        e = RepairRiskCalculated(plan_id="p1", candidate_id="c1", risk_level="low", risk_score=25.0)
        assert e.risk_score == 25.0


class TestRepairConfidenceCalculated:
    def test_create(self):
        e = RepairConfidenceCalculated(plan_id="p1", candidate_id="c1")
        assert e.confidence_dimensions == {}


class TestRepairPlanApproved:
    def test_create(self):
        e = RepairPlanApproved(plan_id="p1", approved_by="admin")
        assert e.approved_by == "admin"


class TestRepairPlanRejected:
    def test_create(self):
        e = RepairPlanRejected(plan_id="p1", rejected_by="admin", reason="too risky")
        assert e.reason == "too risky"


class TestRepairPlanningCompleted:
    def test_create(self):
        e = RepairPlanningCompleted(plan_id="p1", incident_id="i1", selected_candidate_id="c1")
        assert e.selected_candidate_id == "c1"


class TestRepairSimulated:
    def test_create(self):
        e = RepairSimulated(plan_id="p1", simulation_id="s1", overall_outcome="success")
        assert e.overall_outcome == "success"


class TestRepairCostEstimated:
    def test_create(self):
        e = RepairCostEstimated(plan_id="p1", candidate_id="c1", operational_cost=10.5)
        assert e.operational_cost == 10.5


class TestRepairConstraintsChecked:
    def test_create(self):
        e = RepairConstraintsChecked(
            plan_id="p1", hard_constraints_total=3, hard_constraints_satisfied=2
        )
        assert e.hard_constraints_satisfied == 2


class TestRepairValidationCompleted:
    def test_create(self):
        e = RepairValidationCompleted(plan_id="p1", checks_passed=5, checks_failed=1)
        assert e.all_passed is False


class TestRepairKnowledgeConsulted:
    def test_create(self):
        e = RepairKnowledgeConsulted(plan_id="p1", incident_id="i1", similar_incidents_found=3)
        assert e.similar_incidents_found == 3


class TestRepairAttempted:
    def test_create(self):
        e = RepairAttempted(plan_id="p1", incident_id="i1", strategy_id="S01")
        assert e.event_type == "repair_attempted"


class TestRepairSucceeded:
    def test_create(self):
        e = RepairSucceeded(plan_id="p1", duration_seconds=60, strategy_id="S01")
        assert e.duration_seconds == 60


class TestRepairFailed:
    def test_create(self):
        e = RepairFailed(plan_id="p1", failure_reason="timeout", strategy_id="S01")
        assert e.failure_reason == "timeout"


class TestPlannerEventFromDict:
    def test_known_event(self):
        data = {"event_type": "repair_planning_started", "plan_id": "p1"}
        e = planner_event_from_dict(data)
        assert isinstance(e, RepairPlanningStarted)

    def test_unknown_event(self):
        data = {"event_type": "unknown_type"}
        e = planner_event_from_dict(data)
        assert isinstance(e, PlannerDomainEvent)

    def test_all_event_types(self):
        event_types = [
            "repair_planning_started",
            "repair_candidate_generated",
            "repair_risk_calculated",
            "repair_confidence_calculated",
            "repair_plan_approved",
            "repair_plan_rejected",
            "repair_planning_completed",
            "repair_simulated",
            "repair_cost_estimated",
            "repair_constraints_checked",
            "repair_validation_completed",
            "repair_knowledge_consulted",
            "repair_attempted",
            "repair_succeeded",
            "repair_failed",
        ]
        for et in event_types:
            e = planner_event_from_dict({"event_type": et})
            assert e.event_type == et
