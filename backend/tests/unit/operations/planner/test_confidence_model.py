import pytest

from app.operations.planner.domain.analyzers import ConfidenceAnalyzer
from app.operations.planner.domain.enums import RepairType
from app.operations.planner.domain.models import RepairCandidate, RepairGraph, RepairGraphNode


@pytest.fixture
def analyzer():
    return ConfidenceAnalyzer()


@pytest.fixture
def base_candidate():
    return RepairCandidate(
        plan_id="p1",
        repair_type=RepairType.SERVICE_RESTART,
        strategy_id="S01",
        strategy_name="Restart Backend",
        description="Restart the backend",
        affected_components=["backend"],
        prerequisites=["backup_exists"],
    )


class TestConfidenceAnalyzer:
    def test_all_evidence(self, analyzer, base_candidate):
        dims = analyzer.analyze(
            base_candidate,
            root_cause_confidence=0.9,
            evidence_categories={"log", "metric", "config", "system"},
            has_health_check=True,
            has_metrics=True,
            has_logs=True,
            environment="production",
        )
        assert dims.evidence_confidence == 1.0
        assert dims.root_cause_confidence == 0.9
        # compute_overall returns the score but doesn't mutate the frozen model
        overall = dims.compute_overall()
        assert overall > 0.5

    def test_partial_evidence(self, analyzer, base_candidate):
        dims = analyzer.analyze(
            base_candidate,
            root_cause_confidence=0.8,
            evidence_categories={"log", "metric"},
            has_health_check=True,
            has_metrics=False,
            has_logs=False,
            environment="production",
        )
        assert dims.evidence_confidence == 0.5
        assert "Missing evidence category" in dims.evidence_factors[0]

    def test_repair_confidence_with_graph(self, analyzer):
        graph = RepairGraph(
            nodes=[
                RepairGraphNode(
                    node_id="n1", node_type="action", action="restart", command="systemctl restart"
                ),
                RepairGraphNode(
                    node_id="n2",
                    node_type="check",
                    action="health",
                    validation_command="curl localhost",
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
            affected_components=["backend"],
        )
        dims = analyzer.analyze(
            candidate,
            root_cause_confidence=0.8,
            evidence_categories={"log", "metric", "config", "system"},
            has_health_check=True,
            has_metrics=True,
            has_logs=True,
            environment="development",
        )
        assert dims.repair_confidence > 0.5

    def test_repair_confidence_with_steps(self, analyzer):
        from app.operations.planner.domain.models import RepairStep

        candidate = RepairCandidate(
            plan_id="p1",
            repair_type=RepairType.SERVICE_RESTART,
            strategy_id="S01",
            strategy_name="Restart",
            description="Restart",
            steps=[RepairStep(order=1, action="restart", command="systemctl restart")],
            affected_components=["backend"],
        )
        dims = analyzer.analyze(
            candidate,
            root_cause_confidence=0.8,
            evidence_categories={"log"},
            has_health_check=False,
            has_metrics=False,
            has_logs=False,
            environment="development",
        )
        assert dims.repair_confidence > 0.0

    def test_validation_confidence(self, analyzer, base_candidate):
        dims = analyzer.analyze(
            base_candidate,
            root_cause_confidence=0.8,
            evidence_categories={"log"},
            has_health_check=True,
            has_metrics=True,
            has_logs=True,
            environment="development",
        )
        assert dims.validation_confidence > 0.5

    def test_low_root_cause_confidence(self, analyzer, base_candidate):
        dims = analyzer.analyze(
            base_candidate,
            root_cause_confidence=0.2,
            evidence_categories={"log"},
            has_health_check=False,
            has_metrics=False,
            has_logs=False,
            environment="development",
        )
        assert dims.root_cause_confidence == 0.2
        assert any("low" in f.lower() for f in dims.root_cause_factors)

    def test_no_validation_data(self, analyzer, base_candidate):
        dims = analyzer.analyze(
            base_candidate,
            root_cause_confidence=0.8,
            evidence_categories=set(),
            has_health_check=False,
            has_metrics=False,
            has_logs=False,
            environment="development",
        )
        assert dims.validation_confidence == 0.0
        assert any("no validation" in f.lower() for f in dims.validation_factors)
