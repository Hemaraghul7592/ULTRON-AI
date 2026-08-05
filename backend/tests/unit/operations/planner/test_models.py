import pytest
from pydantic import ValidationError

from app.operations.planner.domain.enums import (
    ApprovalLevel,
    ConstraintType,
    RepairGraphNodeType,
    RepairType,
    RiskLevel,
    SimulationOutcome,
)
from app.operations.planner.domain.models import (
    ApprovalRequirement,
    ApprovalStage,
    CandidateSimulation,
    ConfidenceDimensions,
    ExecutionPlan,
    RepairCandidate,
    RepairConstraint,
    RepairCost,
    RepairGraph,
    RepairGraphNode,
    RepairPlan,
    RepairRisk,
    RepairStep,
    RollbackPlan,
    RollbackReadinessCheck,
    SimulationResult,
    ValidationCheck,
    ValidationPipelineResult,
)


class TestRepairGraphNode:
    def test_create_minimal(self):
        node = RepairGraphNode(node_type="action", action="restart")
        assert node.node_type == "action"
        assert node.action == "restart"
        assert node.node_id  # auto-generated UUID
        assert node.command is None
        assert node.parameters == {}
        assert node.dependencies == []
        assert node.timeout_seconds == 300
        assert node.can_fail is False

    def test_frozen(self):
        node = RepairGraphNode(node_type="action", action="restart")
        with pytest.raises(ValidationError):
            node.action = "other"  # type: ignore[misc]

    def test_action_required(self):
        with pytest.raises(ValidationError):
            RepairGraphNode(node_type="action")  # missing action

    def test_action_min_length(self):
        with pytest.raises(ValidationError):
            RepairGraphNode(node_type="action", action="")

    def test_enum_coercion(self):
        node = RepairGraphNode(node_type=RepairGraphNodeType.ACTION, action="test")
        assert node.node_type == "action"  # use_enum_values=True


class TestRepairGraph:
    def test_empty_graph(self):
        graph = RepairGraph()
        assert graph.nodes == []
        assert graph.edges == []
        assert graph.topological_order() == []
        assert graph.parallel_groups() == []
        assert graph.validate_acyclic() is True

    def test_single_node(self):
        node = RepairGraphNode(node_id="n1", node_type="action", action="test")
        graph = RepairGraph(nodes=[node])
        assert graph.topological_order() == ["n1"]
        assert graph.parallel_groups() == [["n1"]]

    def test_linear_dag(self):
        nodes = [
            RepairGraphNode(node_id="n1", node_type="action", action="a"),
            RepairGraphNode(node_id="n2", node_type="action", action="b"),
            RepairGraphNode(node_id="n3", node_type="action", action="c"),
        ]
        graph = RepairGraph(nodes=nodes, edges=[("n1", "n2"), ("n2", "n3")])
        order = graph.topological_order()
        assert order == ["n1", "n2", "n3"]
        assert graph.validate_acyclic() is True

    def test_parallel_nodes(self):
        nodes = [
            RepairGraphNode(node_id="n1", node_type="action", action="a"),
            RepairGraphNode(node_id="n2", node_type="action", action="b"),
            RepairGraphNode(node_id="n3", node_type="check", action="c"),
        ]
        graph = RepairGraph(nodes=nodes, edges=[("n1", "n3"), ("n2", "n3")])
        groups = graph.parallel_groups()
        assert ["n1", "n2"] in groups
        assert ["n3"] in groups

    def test_cyclic_detection(self):
        nodes = [
            RepairGraphNode(node_id="n1", node_type="action", action="a"),
            RepairGraphNode(node_id="n2", node_type="action", action="b"),
        ]
        graph = RepairGraph(nodes=nodes, edges=[("n1", "n2"), ("n2", "n1")])
        assert graph.validate_acyclic() is False


class TestRepairConstraint:
    def test_create(self):
        c = RepairConstraint(
            constraint_type=ConstraintType.MAX_DOWNTIME,
            description="Max 5 min downtime",
        )
        assert c.constraint_type == "max_downtime"
        assert c.severity == "hard"

    def test_frozen(self):
        c = RepairConstraint(
            constraint_type=ConstraintType.NO_DATA_LOSS,
            description="No data loss",
        )
        with pytest.raises(ValidationError):
            c.description = "changed"  # type: ignore[misc]


class TestRepairCost:
    def test_create(self):
        cost = RepairCost(
            execution_time_seconds=60,
            cpu_impact_percent=15.0,
            memory_impact_mb=256.0,
        )
        assert cost.execution_time_seconds == 60
        assert cost.requires_downtime is False


class TestConfidenceDimensions:
    def test_create(self):
        cd = ConfidenceDimensions(
            evidence_confidence=0.8,
            root_cause_confidence=0.9,
            repair_confidence=0.7,
            validation_confidence=0.6,
        )
        assert cd.evidence_confidence == 0.8

    def test_compute_overall(self):
        cd = ConfidenceDimensions(
            evidence_confidence=1.0,
            root_cause_confidence=1.0,
            repair_confidence=1.0,
            validation_confidence=1.0,
        )
        score = cd.compute_overall()
        assert score == 1.0

    def test_compute_overall_weighted(self):
        cd = ConfidenceDimensions(
            evidence_confidence=0.0,
            root_cause_confidence=0.0,
            repair_confidence=1.0,
            validation_confidence=0.0,
        )
        score = cd.compute_overall(w_repair=1.0, w_evidence=0.0, w_root_cause=0.0, w_validation=0.0)
        assert score == 1.0

    def test_bounds(self):
        with pytest.raises(ValidationError):
            ConfidenceDimensions(evidence_confidence=1.5)  # > 1.0
        with pytest.raises(ValidationError):
            ConfidenceDimensions(evidence_confidence=-0.1)  # < 0.0


class TestRepairRisk:
    def test_create(self):
        risk = RepairRisk(score=25.0, level=RiskLevel.LOW)
        assert risk.score == 25.0
        assert risk.level == "low"

    def test_bounds(self):
        with pytest.raises(ValidationError):
            RepairRisk(score=101.0, level=RiskLevel.HIGH)  # > 100
        with pytest.raises(ValidationError):
            RepairRisk(score=-1.0, level=RiskLevel.LOW)  # < 0


class TestCandidateSimulation:
    def test_create(self):
        sim = CandidateSimulation(
            candidate_id="c1",
            plan_id="p1",
            outcome=SimulationOutcome.SUCCESS,
        )
        assert sim.candidate_id == "c1"
        assert sim.outcome == "success"


class TestSimulationResult:
    def test_create(self):
        sr = SimulationResult(plan_id="p1")
        assert sr.plan_id == "p1"
        assert sr.overall_outcome == "unknown"


class TestValidationCheck:
    def test_create(self):
        vc = ValidationCheck(name="health_check", check_type="command")
        assert vc.name == "health_check"
        assert vc.stage == "post_execution"


class TestValidationPipelineResult:
    def test_create(self):
        vpr = ValidationPipelineResult(plan_id="p1")
        assert vpr.plan_id == "p1"
        assert vpr.all_passed is False


class TestRollbackReadinessCheck:
    def test_create(self):
        rrc = RollbackReadinessCheck(plan_id="p1")
        assert rrc.rollback_available is False


class TestRollbackPlan:
    def test_create(self):
        rp = RollbackPlan(plan_id="p1", description="Rollback steps")
        assert rp.plan_id == "p1"
        assert rp.automatic is True
        assert rp.requires_manual_intervention is False


class TestApprovalStage:
    def test_create(self):
        a = ApprovalStage(level=ApprovalLevel.MAINTAINER)
        assert a.level == "maintainer"
        assert a.status == "pending"


class TestApprovalRequirement:
    def test_create(self):
        ar = ApprovalRequirement(
            plan_id="p1",
            final_level=ApprovalLevel.OPERATIONS,
        )
        assert ar.plan_id == "p1"
        assert ar.completed is False


class TestRepairStep:
    def test_create(self):
        s = RepairStep(order=1, action="restart")
        assert s.order == 1
        assert s.can_fail is False


class TestRepairCandidate:
    def test_create(self):
        c = RepairCandidate(
            plan_id="p1",
            repair_type=RepairType.SERVICE_RESTART,
            strategy_id="S01",
            strategy_name="Restart Backend",
            description="Restart the backend service",
        )
        assert c.plan_id == "p1"
        assert c.source == "rule_based"


class TestExecutionPlan:
    def test_create(self):
        ep = ExecutionPlan(plan_id="p1")
        assert ep.plan_id == "p1"
        assert ep.execution_mode == "immediate"


class TestRepairPlan:
    def test_create(self):
        p = RepairPlan(incident_id="inc-1")
        assert p.incident_id == "inc-1"
        assert p.status == "draft"
        assert p.candidates == []

    def test_frozen(self):
        p = RepairPlan(incident_id="inc-1")
        with pytest.raises(ValidationError):
            p.status = "approved"  # type: ignore[misc]
