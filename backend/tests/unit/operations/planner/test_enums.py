from app.operations.planner.domain.enums import (
    ApprovalLevel,
    ConstraintType,
    RepairStatus,
    RepairType,
    RiskLevel,
    SimulationOutcome,
)


class TestRepairStatus:
    def test_all_values(self):
        assert set(RepairStatus) == {
            RepairStatus.DRAFT,
            RepairStatus.CANDIDATES_GENERATED,
            RepairStatus.SIMULATED,
            RepairStatus.RANKED,
            RepairStatus.VALIDATION_PENDING,
            RepairStatus.APPROVAL_PENDING,
            RepairStatus.APPROVED,
            RepairStatus.REJECTED,
            RepairStatus.EXECUTION_READY,
            RepairStatus.EXPIRED,
            RepairStatus.CANCELLED,
            RepairStatus.FAILED,
        }

    def test_string_values(self):
        assert RepairStatus.DRAFT == "draft"
        assert RepairStatus.APPROVED == "approved"
        assert RepairStatus.FAILED == "failed"


class TestRiskLevel:
    def test_all_values(self):
        assert RiskLevel.LOW == "low"
        assert RiskLevel.CATASTROPHIC == "catastrophic"

    def test_member_count(self):
        assert len(RiskLevel) == 5


class TestApprovalLevel:
    def test_all_values(self):
        assert ApprovalLevel.AUTO == "auto"
        assert ApprovalLevel.BLOCKED == "blocked"


class TestRepairType:
    def test_count(self):
        assert len(RepairType) == 18


class TestConstraintType:
    def test_count(self):
        assert len(ConstraintType) == 10


class TestSimulationOutcome:
    def test_all_values(self):
        assert SimulationOutcome.SUCCESS == "success"
        assert SimulationOutcome.UNKNOWN == "unknown"
