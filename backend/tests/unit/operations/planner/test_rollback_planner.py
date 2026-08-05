import pytest

from app.operations.planner.domain.analyzers import RollbackPlanner
from app.operations.planner.domain.enums import RepairType
from app.operations.planner.domain.models import (
    RepairCandidate,
    RepairGraph,
    RepairGraphNode,
    RepairStep,
    RollbackPlan,
)


@pytest.fixture
def planner():
    return RollbackPlanner()


class TestRollbackPlanner:
    def test_generate_from_graph_with_rollback_commands(self, planner):
        graph = RepairGraph(
            nodes=[
                RepairGraphNode(
                    node_id="n1",
                    node_type="action",
                    action="start",
                    rollback_command="systemctl stop backend",
                    estimated_duration_seconds=30,
                ),
                RepairGraphNode(
                    node_id="n2",
                    node_type="check",
                    action="health",
                    rollback_command="systemctl stop healthcheck",
                    estimated_duration_seconds=10,
                ),
            ],
            edges=[("n1", "n2")],
        )
        candidate = RepairCandidate(
            plan_id="p1",
            repair_type=RepairType.SERVICE_RESTART,
            strategy_id="S01",
            strategy_name="Restart",
            description="Restart",
            repair_graph=graph,
        )
        result = planner.generate(candidate, "p1")
        assert isinstance(result, RollbackPlan)
        assert result.automatic is True
        assert len(result.steps) == 2
        assert result.estimated_duration_seconds == 80  # (30*2) + (10*2)

    def test_generate_from_steps_with_rollback_commands(self, planner):
        candidate = RepairCandidate(
            plan_id="p1",
            repair_type=RepairType.SERVICE_RESTART,
            strategy_id="S01",
            strategy_name="Restart",
            description="Restart",
            steps=[
                RepairStep(
                    order=1,
                    action="start",
                    rollback_command="systemctl stop backend",
                    timeout_seconds=30,
                    estimated_duration_seconds=30,
                ),
                RepairStep(
                    order=2,
                    action="health",
                    rollback_command="systemctl stop healthcheck",
                    timeout_seconds=10,
                    estimated_duration_seconds=10,
                ),
            ],
        )
        result = planner.generate(candidate, "p1")
        assert result.automatic is True
        assert len(result.steps) == 2

    def test_generate_manual_rollback_when_no_commands(self, planner):
        candidate = RepairCandidate(
            plan_id="p1",
            repair_type=RepairType.SERVICE_RESTART,
            strategy_id="S01",
            strategy_name="Restart",
            description="Restart",
            steps=[
                RepairStep(order=1, action="start"),
            ],
        )
        result = planner.generate(candidate, "p1")
        assert result.automatic is False
        assert result.requires_manual_intervention is True
        assert "manual" in result.description.lower()

    def test_rollback_graph_has_edges(self, planner):
        graph = RepairGraph(
            nodes=[
                RepairGraphNode(
                    node_id="n1",
                    node_type="action",
                    action="start",
                    rollback_command="stop",
                    estimated_duration_seconds=10,
                ),
                RepairGraphNode(
                    node_id="n2",
                    node_type="check",
                    action="health",
                    rollback_command="stop",
                    estimated_duration_seconds=5,
                ),
            ],
            edges=[("n1", "n2")],
        )
        candidate = RepairCandidate(
            plan_id="p1",
            repair_type=RepairType.SERVICE_RESTART,
            strategy_id="S01",
            strategy_name="Restart",
            description="Restart",
            repair_graph=graph,
        )
        result = planner.generate(candidate, "p1")
        assert result.graph is not None
        assert len(result.graph.edges) == 1
