import pytest

from app.operations.incidents.domain.enums import RootCauseCategory
from app.operations.planner.application.plan_ranker import PlanRanker
from app.operations.planner.application.strategy_selector import StrategySelector
from app.operations.planner.domain.models import KnowledgeSnapshot
from app.operations.planner.domain.strategies import get_strategies_for_category


@pytest.fixture
def selector():
    return StrategySelector()


@pytest.fixture
def ranker():
    return PlanRanker()


class TestStrategySelector:
    def test_select_matching_category(self, selector):
        strategies = get_strategies_for_category(RootCauseCategory.CODE)
        candidates = selector.select(
            strategies,
            root_cause_category="code",
            environment="development",
            severity="warning",
        )
        assert len(candidates) > 0
        assert all(c.repair_type for c in candidates)

    def test_select_no_match_wrong_category(self, selector):
        strategies = get_strategies_for_category(RootCauseCategory.CODE)
        candidates = selector.select(
            strategies,
            root_cause_category="disk",
            environment="development",
            severity="warning",
        )
        assert len(candidates) == 0

    def test_select_no_match_wrong_environment(self, selector):
        strategies = get_strategies_for_category(RootCauseCategory.REDIS)
        # S03 Redis strategy only supports development/staging, but S14 supports production
        # Filter to only S03
        s03_only = [s for s in strategies if s.id == "S03"]
        candidates = selector.select(
            s03_only,
            root_cause_category="redis",
            environment="production",
            severity="warning",
        )
        assert len(candidates) == 0

    def test_select_severity_filter(self, selector):
        strategies = get_strategies_for_category(RootCauseCategory.DEPLOYMENT)
        candidates = selector.select(
            strategies,
            root_cause_category="deployment",
            environment="development",
            severity="info",
        )
        # S10 Rollback requires severity_minimum="high"
        assert len(candidates) == 0

    def test_select_builds_candidate(self, selector):
        strategies = get_strategies_for_category(RootCauseCategory.CODE)
        candidates = selector.select(
            strategies,
            root_cause_category="code",
            environment="development",
            severity="warning",
        )
        for c in candidates:
            assert c.plan_id == ""
            assert c.strategy_id
            assert c.strategy_name
            assert c.description


class TestPlanRanker:
    def test_rank_single_candidate(self, ranker):
        from app.operations.planner.domain.enums import RepairType
        from app.operations.planner.domain.models import RepairCandidate

        candidates = [
            RepairCandidate(
                plan_id="p1",
                repair_type=RepairType.SERVICE_RESTART,
                strategy_id="S01",
                strategy_name="Restart",
                description="Restart",
                estimated_duration_seconds=120,
            ),
        ]
        ranked = ranker.rank(candidates)
        assert len(ranked) == 1
        assert ranked[0].rank == 1
        assert ranked[0].score > 0

    def test_rank_orders_by_score(self, ranker):
        from app.operations.planner.domain.enums import RepairType, RiskLevel
        from app.operations.planner.domain.models import RepairCandidate, RepairRisk

        candidates = [
            RepairCandidate(
                plan_id="p1",
                repair_type=RepairType.SERVICE_RESTART,
                strategy_id="S01",
                strategy_name="Slow Risky",
                description="Slow and risky",
                estimated_duration_seconds=3000,
                risk=RepairRisk(score=90.0, level=RiskLevel.CRITICAL),
                affected_components=["a", "b", "c", "d", "e"],
            ),
            RepairCandidate(
                plan_id="p1",
                repair_type=RepairType.NETWORK_CHECK,
                strategy_id="S07",
                strategy_name="Fast Safe",
                description="Fast and safe",
                estimated_duration_seconds=30,
                risk=RepairRisk(score=10.0, level=RiskLevel.LOW),
            ),
        ]
        ranked = ranker.rank(candidates)
        assert ranked[0].strategy_id == "S07"
        assert ranked[1].strategy_id == "S01"
        assert ranked[0].rank == 1
        assert ranked[1].rank == 2

    def test_rank_with_knowledge(self, ranker):
        from app.operations.planner.domain.enums import RepairType
        from app.operations.planner.domain.models import RepairCandidate

        knowledge = KnowledgeSnapshot(
            incident_id="i1",
            root_cause_category="code",
            historical_success_rates={"S01": 0.9, "S07": 0.3},
        )
        candidates = [
            RepairCandidate(
                plan_id="p1",
                repair_type=RepairType.SERVICE_RESTART,
                strategy_id="S01",
                strategy_name="Restart",
                description="Restart",
            ),
            RepairCandidate(
                plan_id="p1",
                repair_type=RepairType.NETWORK_CHECK,
                strategy_id="S07",
                strategy_name="Network",
                description="Network",
            ),
        ]
        ranked = ranker.rank(candidates, knowledge)
        assert ranked[0].strategy_id == "S01"
