import pytest

from app.operations.planner.domain.analyzers import CostEstimator
from app.operations.planner.domain.enums import RepairType


@pytest.fixture
def estimator():
    return CostEstimator()


class TestCostEstimator:
    def test_service_restart(self, estimator):
        cost = estimator.estimate(
            RepairType.SERVICE_RESTART,
            estimated_duration_seconds=120,
            affected_components=["backend"],
        )
        assert cost.execution_time_seconds == 120
        assert cost.cpu_impact_percent == 10.0
        assert cost.memory_impact_mb == 50.0
        assert cost.requires_downtime is True
        assert cost.downtime_seconds == 120

    def test_database_maintenance(self, estimator):
        cost = estimator.estimate(
            RepairType.DATABASE_MAINTENANCE,
            estimated_duration_seconds=300,
            affected_components=["database"],
        )
        assert cost.cpu_impact_percent == 25.0
        assert cost.memory_impact_mb == 200.0
        assert cost.storage_impact_mb == 100.0
        assert cost.requires_downtime is True

    def test_disk_cleanup(self, estimator):
        cost = estimator.estimate(
            RepairType.DISK_CLEANUP,
            estimated_duration_seconds=60,
            affected_components=["disk"],
        )
        assert cost.storage_impact_mb == 500.0
        assert cost.requires_downtime is False

    def test_network_check(self, estimator):
        cost = estimator.estimate(
            RepairType.NETWORK_CHECK,
            estimated_duration_seconds=30,
            affected_components=["network"],
        )
        assert cost.network_impact == "medium"
        assert cost.requires_downtime is False

    def test_manual_intervention(self, estimator):
        cost = estimator.estimate(
            RepairType.MANUAL_INTERVENTION,
            estimated_duration_seconds=0,
            affected_components=[],
        )
        assert cost.human_effort_hours == 2.0
        assert cost.cpu_impact_percent == 0.0

    def test_configuration_change(self, estimator):
        cost = estimator.estimate(
            RepairType.CONFIGURATION_CHANGE,
            estimated_duration_seconds=180,
            affected_components=["backend"],
        )
        assert cost.human_effort_hours == 0.5
        assert cost.requires_downtime is False

    def test_code_revert(self, estimator):
        cost = estimator.estimate(
            RepairType.CODE_REVERT,
            estimated_duration_seconds=180,
            affected_components=["backend", "code"],
        )
        assert cost.human_effort_hours == 0.5
        assert cost.requires_downtime is True

    def test_operational_cost_bounded(self, estimator):
        cost = estimator.estimate(
            RepairType.DATABASE_MAINTENANCE,
            estimated_duration_seconds=3600,
            affected_components=["database", "backend", "redis"],
        )
        assert cost.operational_cost <= 100.0

    def test_resource_scaling(self, estimator):
        cost = estimator.estimate(
            RepairType.RESOURCE_SCALING,
            estimated_duration_seconds=180,
            affected_components=["cpu"],
        )
        assert cost.cpu_impact_percent == 5.0
        assert cost.requires_downtime is False
