import pytest

from app.operations.incidents.domain.enums import RootCauseCategory
from app.operations.planner.domain.analyzers import RiskAnalyzer
from app.operations.planner.domain.enums import RepairType, RiskLevel
from app.operations.planner.domain.models import RepairCandidate


@pytest.fixture
def analyzer():
    return RiskAnalyzer()


@pytest.fixture
def base_candidate():
    return RepairCandidate(
        plan_id="p1",
        repair_type=RepairType.SERVICE_RESTART,
        strategy_id="S01",
        strategy_name="Restart Backend",
        description="Restart the backend",
        affected_components=["backend"],
    )


class TestRiskAnalyzer:
    def test_low_risk_dev_environment(self, analyzer, base_candidate):
        risk = analyzer.analyze(
            base_candidate,
            component_type="backend",
            environment="development",
            root_cause_category=RootCauseCategory.CODE,
            root_cause_confidence=0.9,
        )
        assert risk.score <= 50  # Dev + code + 1 component + short duration + high confidence
        assert risk.requires_backup is False

    def test_medium_risk_staging(self, analyzer, base_candidate):
        risk = analyzer.analyze(
            base_candidate,
            component_type="backend",
            environment="staging",
            root_cause_category=RootCauseCategory.CODE,
            root_cause_confidence=0.9,
        )
        assert risk.level == RiskLevel.MEDIUM
        assert 20 < risk.score <= 50

    def test_high_risk_production_critical_service(self, analyzer):
        candidate = RepairCandidate(
            plan_id="p1",
            repair_type=RepairType.DATABASE_MAINTENANCE,
            strategy_id="S02",
            strategy_name="Restart DB",
            description="Restart database",
            affected_components=["database", "backend", "redis"],
            estimated_duration_seconds=600,
        )
        risk = analyzer.analyze(
            candidate,
            component_type="database",
            environment="production",
            root_cause_category=RootCauseCategory.DATABASE,
            root_cause_confidence=0.3,
        )
        assert risk.level in (RiskLevel.HIGH, RiskLevel.CRITICAL)
        assert risk.requires_backup is True
        assert risk.requires_maintenance_window is True
        assert risk.downtime_estimate_seconds == 600

    def test_blast_radius(self, analyzer, base_candidate):
        candidate = base_candidate.model_copy(
            update={"affected_components": ["backend", "database", "redis", "nginx"]}
        )
        risk = analyzer.analyze(
            candidate,
            component_type="backend",
            environment="development",
            root_cause_category=RootCauseCategory.CODE,
            root_cause_confidence=0.9,
        )
        assert risk.blast_radius == ["backend", "database", "redis", "nginx"]

    def test_low_confidence_increases_risk(self, analyzer, base_candidate):
        risk = analyzer.analyze(
            base_candidate,
            component_type="backend",
            environment="development",
            root_cause_category=RootCauseCategory.CODE,
            root_cause_confidence=0.2,
        )
        assert risk.score > 10
        assert any("confidence" in f.lower() for f in risk.factors)

    def test_mitigations_for_high_risk(self, analyzer):
        candidate = RepairCandidate(
            plan_id="p1",
            repair_type=RepairType.DATABASE_MAINTENANCE,
            strategy_id="S02",
            strategy_name="Restart DB",
            description="Restart database",
            affected_components=["database", "backend", "redis", "cache"],
            estimated_duration_seconds=600,
        )
        risk = analyzer.analyze(
            candidate,
            component_type="database",
            environment="production",
            root_cause_category=RootCauseCategory.DATABASE,
            root_cause_confidence=0.2,
        )
        assert any("backup" in m.lower() for m in risk.mitigations)
        assert any("maintenance" in m.lower() for m in risk.mitigations)

    def test_score_clamped_to_100(self, analyzer):
        candidate = RepairCandidate(
            plan_id="p1",
            repair_type=RepairType.DATABASE_MAINTENANCE,
            strategy_id="S02",
            strategy_name="Restart DB",
            description="Restart database",
            affected_components=["a", "b", "c", "d", "e", "f", "g", "h"],
            estimated_duration_seconds=1000,
        )
        risk = analyzer.analyze(
            candidate,
            component_type="database",
            environment="production",
            root_cause_category=RootCauseCategory.DATABASE,
            root_cause_confidence=0.1,
        )
        assert risk.score <= 100.0
