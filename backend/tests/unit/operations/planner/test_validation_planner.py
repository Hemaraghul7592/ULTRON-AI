import pytest

from app.operations.planner.domain.analyzers import ValidationPlanner
from app.operations.planner.domain.enums import RiskLevel
from app.operations.planner.domain.models import (
    RepairCandidate,
    RepairPlan,
    RepairRisk,
    RollbackPlan,
    RollbackReadinessCheck,
    ValidationPipelineResult,
)


@pytest.fixture
def planner():
    return ValidationPlanner()


class TestValidationPlanner:
    def test_pre_approval_checks_with_candidate(self, planner):
        plan = RepairPlan(
            incident_id="i1",
            selected_candidate=RepairCandidate(
                plan_id="p1",
                repair_type="service_restart",
                strategy_id="S01",
                strategy_name="Restart",
                description="Restart",
            ),
        )
        result = planner.generate_pre_approval_checks(plan)
        assert isinstance(result, ValidationPipelineResult)
        assert result.plan_id == plan.plan_id
        assert len(result.checks) >= 2

    def test_production_extra_checks(self, planner):
        plan = RepairPlan(
            incident_id="i1",
            environment="production",
            selected_candidate=RepairCandidate(
                plan_id="p1",
                repair_type="service_restart",
                strategy_id="S01",
                strategy_name="Restart",
                description="Restart",
            ),
        )
        result = planner.generate_pre_approval_checks(plan)
        check_names = [c.name for c in result.checks]
        assert "production_safety" in check_names

    def test_low_risk_passes(self, planner):
        plan = RepairPlan(
            incident_id="i1",
            selected_candidate=RepairCandidate(
                plan_id="p1",
                repair_type="service_restart",
                strategy_id="S01",
                strategy_name="Restart",
                description="Restart",
                risk=RepairRisk(score=10.0, level=RiskLevel.LOW),
            ),
        )
        result = planner.generate_pre_approval_checks(plan)
        assert result.all_passed is True

    def test_high_risk_fails(self, planner):
        plan = RepairPlan(
            incident_id="i1",
            selected_candidate=RepairCandidate(
                plan_id="p1",
                repair_type="service_restart",
                strategy_id="S01",
                strategy_name="Restart",
                description="Restart",
                risk=RepairRisk(score=80.0, level=RiskLevel.HIGH),
            ),
        )
        result = planner.generate_pre_approval_checks(plan)
        assert result.all_passed is False
        assert len(result.failed) > 0

    def test_rollback_readiness_with_rollback(self, planner):
        from app.operations.planner.domain.enums import RepairGraphNodeType
        from app.operations.planner.domain.models import RepairGraphNode

        plan = RepairPlan(
            incident_id="i1",
            rollback_plan=RollbackPlan(
                plan_id="p1",
                description="Rollback steps",
                steps=[
                    RepairGraphNode(
                        node_type=RepairGraphNodeType.ROLLBACK,
                        action="rollback_restart",
                        command="systemctl stop backend",
                    ),
                ],
                estimated_duration_seconds=60,
                automatic=True,
            ),
        )
        result = planner.check_rollback_readiness(plan)
        assert isinstance(result, RollbackReadinessCheck)
        assert result.rollback_available is True
        assert result.rollback_automatic is True
        assert result.rollback_steps_total == 1

    def test_rollback_readiness_no_rollback(self, planner):
        plan = RepairPlan(incident_id="i1")
        result = planner.check_rollback_readiness(plan)
        assert result.rollback_available is False
        assert "No rollback plan available" in result.issues

    def test_rollback_not_automatic(self, planner):
        from app.operations.planner.domain.enums import RepairGraphNodeType
        from app.operations.planner.domain.models import RepairGraphNode

        plan = RepairPlan(
            incident_id="i1",
            rollback_plan=RollbackPlan(
                plan_id="p1",
                description="Manual rollback",
                steps=[
                    RepairGraphNode(
                        node_type=RepairGraphNodeType.ROLLBACK,
                        action="manual",
                    ),
                ],
                automatic=False,
            ),
        )
        result = planner.check_rollback_readiness(plan)
        assert "Rollback is not automatic" in result.issues
