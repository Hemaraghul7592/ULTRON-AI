from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.operations.incidents.domain.enums import RootCauseCategory
from app.operations.incidents.domain.events import InvestigationCompleted
from app.operations.planner.application.planning_service import RepairPlanningService
from app.operations.planner.infrastructure.repositories import SQLAlchemyPlanRepository

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from app.operations.core.event_bus import EventBus, EventSubscription
    from app.operations.planner.application.ports import (
        ConfidenceAnalyzerPort,
        ConstraintEnginePort,
        CostEstimatorPort,
        PlannerEventPublisher,
        RepairStrategyProvider,
        RiskAnalyzerPort,
        RollbackPlannerPort,
        SimulationEnginePort,
        ValidationPipelinePort,
    )

logger = logging.getLogger(__name__)


class PlannerSubscriber:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        strategy_provider: RepairStrategyProvider,
        risk_analyzer: RiskAnalyzerPort,
        confidence_analyzer: ConfidenceAnalyzerPort,
        cost_estimator: CostEstimatorPort,
        constraint_engine: ConstraintEnginePort,
        knowledge_adapter: object,
        simulation_engine: SimulationEnginePort,
        rollback_planner: RollbackPlannerPort,
        validation_pipeline: ValidationPipelinePort,
        approval_policy: object,
        publisher: PlannerEventPublisher | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._strategy_provider = strategy_provider
        self._risk_analyzer = risk_analyzer
        self._confidence_analyzer = confidence_analyzer
        self._cost_estimator = cost_estimator
        self._constraint_engine = constraint_engine
        self._knowledge_adapter = knowledge_adapter
        self._simulation_engine = simulation_engine
        self._rollback_planner = rollback_planner
        self._validation_pipeline = validation_pipeline
        self._approval_policy = approval_policy
        self._publisher = publisher
        self._subscription: EventSubscription | None = None

    def start(self, event_bus: EventBus) -> None:
        self._subscription = event_bus.subscribe(
            InvestigationCompleted, self._on_investigation_completed
        )

    def stop(self, event_bus: EventBus) -> None:
        if self._subscription is not None:
            event_bus.unsubscribe(self._subscription)
            self._subscription = None

    async def _on_investigation_completed(self, event: InvestigationCompleted) -> None:
        try:
            result = event.investigation_result
            if result.root_cause is None:
                return
            if result.root_cause.category == RootCauseCategory.UNKNOWN:
                return

            async with self._session_factory() as session:
                repository = SQLAlchemyPlanRepository(session)
                service = RepairPlanningService(
                    repository=repository,
                    strategy_provider=self._strategy_provider,
                    risk_analyzer=self._risk_analyzer,
                    confidence_analyzer=self._confidence_analyzer,
                    cost_estimator=self._cost_estimator,
                    constraint_engine=self._constraint_engine,
                    knowledge_adapter=self._knowledge_adapter,
                    simulation_engine=self._simulation_engine,
                    rollback_planner=self._rollback_planner,
                    validation_pipeline=self._validation_pipeline,
                    approval_policy=self._approval_policy,
                    publisher=self._publisher,
                )

                from app.operations.incidents.infrastructure.repositories import (
                    SQLAlchemyIncidentRepositoryV3,
                )

                inc_repo = SQLAlchemyIncidentRepositoryV3(session)
                incident = await inc_repo.get(result.incident_id)
                if incident is None:
                    return

                evidence = await inc_repo.get_evidence(result.incident_id)
                evidence_categories = {e.category.value for e in evidence}
                has_health = any(e.category.value == "system" for e in evidence)
                has_metrics = any(e.category.value == "metric" for e in evidence)
                has_logs = any(e.category.value == "log" for e in evidence)

                plan = await service.plan(
                    incident_id=result.incident_id,
                    root_cause=result.root_cause,
                    incident=incident,
                    evidence_categories=evidence_categories,
                    has_health_check=has_health,
                    has_metrics=has_metrics,
                    has_logs=has_logs,
                )
                await session.commit()
                logger.info(
                    "Repair plan generated for incident %s: plan %s",
                    result.incident_id,
                    plan.plan_id,
                )
        except Exception:
            logger.exception("Repair planning failed for incident from investigation")
