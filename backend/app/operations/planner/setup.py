from __future__ import annotations

from typing import TYPE_CHECKING

from app.operations.planner.application.knowledge_adapter import KnowledgeAdapter
from app.operations.planner.application.publisher import InMemoryPlannerPublisher
from app.operations.planner.application.simulation_service import SimulationService
from app.operations.planner.application.subscriber import PlannerSubscriber
from app.operations.planner.domain.confidence_model import ConfidenceAnalyzer
from app.operations.planner.domain.constraint_model import ConstraintEngine
from app.operations.planner.domain.cost_model import CostEstimator
from app.operations.planner.domain.risk_model import RiskAnalyzer
from app.operations.planner.domain.rollback_planner import RollbackPlanner
from app.operations.planner.domain.strategies import get_all_strategies
from app.operations.planner.domain.validation_planner import ValidationPlanner

if TYPE_CHECKING:
    from app.operations.core.runtime import OperationsRuntime


class _StrategyProvider:
    def get_all_strategies(self) -> list:  # type: ignore[override]
        return get_all_strategies()

    def get_strategies_for_category(self, category: str) -> list:  # type: ignore[override]
        from app.operations.incidents.domain.enums import RootCauseCategory
        from app.operations.planner.domain.strategies import get_strategies_for_category

        return get_strategies_for_category(RootCauseCategory(category))


class _ApprovalPolicy:
    def determine_level(
        self,
        risk_level: str,
        confidence_score: float,
        environment: str,
    ) -> str:
        from app.operations.planner.domain.enums import ApprovalLevel

        if risk_level == "catastrophic":
            return ApprovalLevel.BLOCKED.value
        if confidence_score < 0.2:
            return ApprovalLevel.BLOCKED.value
        if risk_level == "critical":
            return ApprovalLevel.ADMINISTRATOR.value
        if risk_level == "high":
            return ApprovalLevel.MAINTAINER.value
        if environment == "production" and risk_level == "medium":
            return ApprovalLevel.OPERATIONS.value
        if (
            risk_level in ("low", "medium")
            and confidence_score >= 0.7
            and environment != "production"
        ):
            return ApprovalLevel.AUTO.value
        return ApprovalLevel.MAINTAINER.value


async def setup_repair_planner(
    runtime: OperationsRuntime,
) -> PlannerSubscriber:
    publisher = InMemoryPlannerPublisher()

    subscriber = PlannerSubscriber(
        session_factory=runtime.session_factory,
        strategy_provider=_StrategyProvider(),  # type: ignore[arg-type]
        risk_analyzer=RiskAnalyzer(),  # type: ignore[arg-type]
        confidence_analyzer=ConfidenceAnalyzer(),  # type: ignore[arg-type]
        cost_estimator=CostEstimator(),  # type: ignore[arg-type]
        constraint_engine=ConstraintEngine(),  # type: ignore[arg-type]
        knowledge_adapter=KnowledgeAdapter(),  # type: ignore[arg-type]
        simulation_engine=SimulationService(),  # type: ignore[arg-type]
        rollback_planner=RollbackPlanner(),  # type: ignore[arg-type]
        validation_pipeline=ValidationPlanner(),  # type: ignore[arg-type]
        approval_policy=_ApprovalPolicy(),  # type: ignore[arg-type]
        publisher=publisher,
    )
    subscriber.start(runtime.event_bus)

    runtime.planner_subscriber = subscriber
    runtime.planner_publisher = publisher
    return subscriber
