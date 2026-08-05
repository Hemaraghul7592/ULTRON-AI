import pytest

from app.operations.planner.domain.analyzers import ConstraintEngine
from app.operations.planner.domain.enums import ConstraintType, RepairType
from app.operations.planner.domain.models import RepairCandidate, RepairConstraint


@pytest.fixture
def engine():
    return ConstraintEngine()


class TestConstraintEngine:
    def test_production_constraints(self, engine):
        constraints = engine.evaluate("backend", "production", "warning")
        types = [c.constraint_type for c in constraints]
        assert ConstraintType.REQUIRES_HUMAN_APPROVAL in types
        assert ConstraintType.REQUIRES_BACKUP in types

    def test_critical_severity_constraints(self, engine):
        constraints = engine.evaluate("backend", "development", "critical")
        types = [c.constraint_type for c in constraints]
        assert ConstraintType.MAX_DOWNTIME in types

    def test_database_data_loss_constraint(self, engine):
        constraints = engine.evaluate("database", "development", "warning")
        types = [c.constraint_type for c in constraints]
        assert ConstraintType.NO_DATA_LOSS in types

    def test_redis_data_loss_constraint(self, engine):
        constraints = engine.evaluate("redis", "development", "warning")
        types = [c.constraint_type for c in constraints]
        assert ConstraintType.NO_DATA_LOSS in types

    def test_dev_no_extra_constraints(self, engine):
        constraints = engine.evaluate("backend", "development", "info")
        assert len(constraints) == 0

    def test_satisfies_all_met(self, engine):
        candidate = RepairCandidate(
            plan_id="p1",
            repair_type=RepairType.SERVICE_RESTART,
            strategy_id="S01",
            strategy_name="Restart",
            description="Restart",
            estimated_duration_seconds=60,
        )
        constraints = [
            RepairConstraint(
                constraint_type=ConstraintType.MAX_DOWNTIME,
                description="Max downtime",
                parameters={"max_seconds": "300"},
                severity="hard",
            ),
        ]
        ok, violations = engine.satisfies(candidate, constraints)
        assert ok is True
        assert violations == []

    def test_violates_max_downtime(self, engine):
        candidate = RepairCandidate(
            plan_id="p1",
            repair_type=RepairType.SERVICE_RESTART,
            strategy_id="S01",
            strategy_name="Restart",
            description="Restart",
            estimated_duration_seconds=600,
        )
        constraints = [
            RepairConstraint(
                constraint_type=ConstraintType.MAX_DOWNTIME,
                description="Max downtime",
                parameters={"max_seconds": "300"},
                severity="hard",
            ),
        ]
        ok, violations = engine.satisfies(candidate, constraints)
        assert ok is False
        assert len(violations) == 1

    def test_soft_constraints_ignored(self, engine):
        candidate = RepairCandidate(
            plan_id="p1",
            repair_type=RepairType.CODE_REVERT,
            strategy_id="S11",
            strategy_name="Revert",
            description="Revert",
        )
        constraints = [
            RepairConstraint(
                constraint_type=ConstraintType.NO_DATA_LOSS,
                description="No data loss",
                severity="soft",
            ),
        ]
        ok, violations = engine.satisfies(candidate, constraints)
        assert ok is True

    def test_no_data_loss_violation(self, engine):
        candidate = RepairCandidate(
            plan_id="p1",
            repair_type=RepairType.CODE_REVERT,
            strategy_id="S11",
            strategy_name="Revert",
            description="Revert",
        )
        constraints = [
            RepairConstraint(
                constraint_type=ConstraintType.NO_DATA_LOSS,
                description="No data loss",
                severity="hard",
            ),
        ]
        ok, violations = engine.satisfies(candidate, constraints)
        assert ok is False
