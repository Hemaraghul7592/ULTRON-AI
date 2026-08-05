from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from app.operations.domain.value_objects import utc_now
from app.operations.planner.domain.events import (
    RepairCandidateGenerated,
    RepairConfidenceCalculated,
    RepairCostEstimated,
    RepairKnowledgeConsulted,
    RepairPlanningCompleted,
    RepairPlanningStarted,
    RepairRiskCalculated,
    RepairSimulated,
)
from app.operations.planner.domain.models import (
    ApprovalRequirement,
    ApprovalStage,
    ExecutionPlan,
    RepairPlan,
    RepairStatus,
)
from app.operations.planner.domain.repair_graph import build_graph_from_strategy

if TYPE_CHECKING:
    from app.operations.incidents.domain.models import Incident, RootCause
    from app.operations.planner.application.ports import (
        ConfidenceAnalyzerPort,
        ConstraintEnginePort,
        CostEstimatorPort,
        PlannerEventPublisher,
        PlanRepository,
        RepairStrategyProvider,
        RiskAnalyzerPort,
        RollbackPlannerPort,
        SimulationEnginePort,
        ValidationPipelinePort,
    )
    from app.operations.planner.domain.models import (
        ApprovalLevel,
        KnowledgeSnapshot,
    )

logger = logging.getLogger(__name__)


class RepairPlanningService:
    def __init__(
        self,
        repository: PlanRepository,
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
        self._repository = repository
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

    async def plan(
        self,
        incident_id: str,
        root_cause: RootCause,
        incident: Incident,
        evidence_categories: set[str] | None = None,
        has_health_check: bool = False,
        has_metrics: bool = False,
        has_logs: bool = False,
    ) -> RepairPlan:
        started_at = time.perf_counter()

        plan = RepairPlan(
            incident_id=incident_id,
            environment=incident.environment,
            component_type=incident.component_type,
            component_name=incident.component_name,
        )
        await self._repository.save(plan)

        await self._publish(RepairPlanningStarted(plan_id=plan.plan_id, incident_id=incident_id))

        # Stage 1: Knowledge consultation
        knowledge_snapshot = await self._consult_knowledge(
            plan.plan_id, incident_id, root_cause, incident
        )

        # Stage 2: Strategy selection
        strategies = self._strategy_provider.get_all_strategies()
        from app.operations.planner.application.strategy_selector import StrategySelector

        selector = StrategySelector()
        candidates = selector.select(
            strategies=strategies,
            root_cause_category=root_cause.category.value,
            environment=incident.environment,
            severity=incident.severity,
            knowledge_snapshot=knowledge_snapshot,
        )

        # Set plan_id on candidates
        candidates = [c.model_copy(update={"plan_id": plan.plan_id}) for c in candidates]

        # Add graph to candidates that have strategy templates
        for candidate in candidates:
            strategy = next((s for s in strategies if s.id == candidate.strategy_id), None)
            if strategy and strategy.steps_template:
                graph = build_graph_from_strategy(
                    strategy.steps_template,
                    target=incident.component_name,
                    estimated_duration=strategy.estimated_duration_seconds,
                )
                candidate = candidate.model_copy(update={"repair_graph": graph})
                # Update in list
                candidates = [
                    candidate if c.candidate_id == candidate.candidate_id else c for c in candidates
                ]

        # Publish candidate events
        for candidate in candidates:
            await self._publish(
                RepairCandidateGenerated(
                    plan_id=plan.plan_id,
                    candidate_id=candidate.candidate_id,
                    strategy_id=candidate.strategy_id,
                    repair_type=candidate.repair_type.value,
                )
            )

        plan = plan.model_copy(
            update={
                "candidates": candidates,
                "total_candidates_evaluated": len(candidates),
                "knowledge_consulted": knowledge_snapshot is not None,
                "knowledge_snapshot_id": (
                    knowledge_snapshot.snapshot_id if knowledge_snapshot else None
                ),
                "status": RepairStatus.CANDIDATES_GENERATED,
            }
        )

        if not candidates:
            plan = plan.model_copy(update={"status": RepairStatus.FAILED})
            await self._repository.save(plan)
            return plan

        # Stage 3: Risk analysis
        risk_scores: dict[str, float] = {}
        for candidate in candidates:
            risk = self._risk_analyzer.analyze(
                candidate=candidate,
                component_type=incident.component_type,
                environment=incident.environment,
                root_cause_category=root_cause.category,
                root_cause_confidence=root_cause.confidence.value,
            )
            candidate = candidate.model_copy(update={"risk": risk})
            risk_scores[candidate.candidate_id] = risk.score
            candidates = [
                candidate if c.candidate_id == candidate.candidate_id else c for c in candidates
            ]
            await self._publish(
                RepairRiskCalculated(
                    plan_id=plan.plan_id,
                    candidate_id=candidate.candidate_id,
                    risk_level=risk.level.value,
                    risk_score=risk.score,
                )
            )

        plan = plan.model_copy(update={"status": RepairStatus.RISK_CALCULATED})

        # Stage 4: Cost estimation
        for candidate in candidates:
            cost = self._cost_estimator.estimate(
                repair_type=candidate.repair_type.value,
                estimated_duration_seconds=candidate.estimated_duration_seconds,
                affected_components=candidate.affected_components,
            )
            candidate = candidate.model_copy(update={"cost": cost})
            candidates = [
                candidate if c.candidate_id == candidate.candidate_id else c for c in candidates
            ]
            await self._publish(
                RepairCostEstimated(
                    plan_id=plan.plan_id,
                    candidate_id=candidate.candidate_id,
                    operational_cost=cost.operational_cost,
                    downtime_seconds=cost.downtime_seconds,
                )
            )

        # Stage 5: Confidence analysis
        evidence_cats = evidence_categories or set()
        for candidate in candidates:
            confidence = self._confidence_analyzer.analyze(
                candidate=candidate,
                root_cause_confidence=root_cause.confidence.value,
                evidence_categories=evidence_cats,
                has_health_check=has_health_check,
                has_metrics=has_metrics,
                has_logs=has_logs,
                environment=incident.environment,
            )
            candidate = candidate.model_copy(update={"confidence": confidence})
            candidates = [
                candidate if c.candidate_id == candidate.candidate_id else c for c in candidates
            ]
            await self._publish(
                RepairConfidenceCalculated(
                    plan_id=plan.plan_id,
                    candidate_id=candidate.candidate_id,
                    confidence_dimensions=confidence.dimension_scores,
                )
            )

        plan = plan.model_copy(update={"status": RepairStatus.CONFIDENCE_CALCULATED})

        # Stage 6: Simulation
        sim_result = self._simulation_engine.simulate_all(
            candidates=candidates,
            environment=incident.environment,
            risk_scores=risk_scores,
        )
        # Update candidates with simulation results
        for sim in sim_result.candidate_simulations:
            for i, candidate in enumerate(candidates):
                if candidate.candidate_id == sim.candidate_id:
                    candidates[i] = candidate.model_copy(update={"simulation": sim})
                    break

        plan = plan.model_copy(
            update={
                "simulation_result": sim_result,
                "status": RepairStatus.SIMULATED,
            }
        )
        await self._publish(
            RepairSimulated(
                plan_id=plan.plan_id,
                simulation_id=sim_result.result_id,
                overall_outcome=sim_result.overall_outcome.value,
                candidate_count=len(candidates),
            )
        )

        # Stage 7: Constraint checking
        constraints = self._constraint_engine.evaluate(
            component_type=incident.component_type,
            environment=incident.environment,
            severity=incident.severity,
        )
        plan = plan.model_copy(update={"constraints": constraints})

        # Stage 8: Ranking
        from app.operations.planner.application.plan_ranker import PlanRanker

        ranker = PlanRanker()
        candidates = ranker.rank(candidates, knowledge_snapshot)
        plan = plan.model_copy(update={"candidates": candidates, "status": RepairStatus.RANKED})

        # Stage 9: Select best candidate
        selected = candidates[0] if candidates else None
        if selected is None:
            plan = plan.model_copy(update={"status": RepairStatus.FAILED})
            await self._repository.save(plan)
            return plan

        # Stage 10: Rollback planning
        rollback = self._rollback_planner.generate(selected, plan.plan_id)

        # Stage 11: Validation
        plan = plan.model_copy(update={"selected_candidate": selected})
        validation = self._validation_pipeline.generate_pre_approval_checks(plan)

        # Stage 12: Approval
        approval_level = self._determine_approval(selected, incident.environment)
        approval = ApprovalRequirement(
            plan_id=plan.plan_id,
            stages=[
                ApprovalStage(
                    level=approval_level,
                    timeout_hours=24,
                )
            ],
            final_level=approval_level,
        )

        # Build execution plan
        execution = ExecutionPlan(
            plan_id=plan.plan_id,
            repair_graph=selected.repair_graph,
            rollback=rollback,
            validation=validation,
            constraints=constraints,
            cost=selected.cost,
        )

        # Final plan
        utc_now()
        duration_ms = int((time.perf_counter() - started_at) * 1000)

        plan = plan.model_copy(
            update={
                "selected_candidate": selected,
                "rollback_plan": rollback,
                "validation": validation,
                "approval": approval,
                "execution_plan": execution,
                "strategy_used": selected.strategy_name,
                "planning_duration_ms": duration_ms,
                "status": (
                    RepairStatus.APPROVAL_PENDING
                    if approval_level.value not in ("auto",)
                    else RepairStatus.EXECUTION_READY
                ),
            }
        )

        if approval_level.value == "auto":
            plan = plan.model_copy(
                update={
                    "status": RepairStatus.EXECUTION_READY,
                    "approval": ApprovalRequirement(
                        plan_id=plan.plan_id,
                        stages=[],
                        final_level=approval_level,
                        completed=True,
                        approved=True,
                    ),
                }
            )

        await self._repository.save(plan)

        await self._publish(
            RepairPlanningCompleted(
                plan_id=plan.plan_id,
                incident_id=incident_id,
                selected_candidate_id=selected.candidate_id,
                risk_level=selected.risk.level.value if selected.risk else "unknown",
                confidence_dimensions=(
                    selected.confidence.dimension_scores if selected.confidence else {}
                ),
                approval_level=approval_level.value,
                planning_duration_ms=duration_ms,
            )
        )

        return plan

    async def _consult_knowledge(
        self,
        plan_id: str,
        incident_id: str,
        root_cause: RootCause,
        incident: Incident,
    ) -> KnowledgeSnapshot | None:
        from app.operations.planner.application.knowledge_adapter import (
            KnowledgeAdapter,
        )

        if not isinstance(self._knowledge_adapter, KnowledgeAdapter):
            return None
        try:
            snapshot = await self._knowledge_adapter.consult(
                incident_id=incident_id,
                root_cause_category=root_cause.category.value,
                component_type=incident.component_type,
                environment=incident.environment,
            )
            await self._publish(
                RepairKnowledgeConsulted(
                    plan_id=plan_id,
                    incident_id=incident_id,
                    similar_incidents_found=len(snapshot.similar_incidents),
                    strategies_informed=list(snapshot.historical_success_rates.keys()),
                )
            )
            return snapshot
        except Exception:
            logger.exception("Knowledge consultation failed")
            return None

    def _determine_approval(
        self,
        candidate: object,
        environment: str,
    ) -> ApprovalLevel:
        from app.operations.planner.domain.enums import ApprovalLevel

        risk = getattr(candidate, "risk", None)
        confidence = getattr(candidate, "confidence", None)

        risk_level = getattr(risk, "level", "medium") if risk else "medium"
        conf_score = getattr(confidence, "overall_score", 0.5) if confidence else 0.5

        if risk_level == "catastrophic":
            return ApprovalLevel.BLOCKED
        if conf_score < 0.2:
            return ApprovalLevel.BLOCKED
        if risk_level == "critical":
            return ApprovalLevel.ADMINISTRATOR
        if risk_level == "high":
            return ApprovalLevel.MAINTAINER
        if environment == "production" and risk_level == "medium":
            return ApprovalLevel.OPERATIONS
        if risk_level in ("low", "medium") and conf_score >= 0.7 and environment != "production":
            return ApprovalLevel.AUTO
        return ApprovalLevel.MAINTAINER

    async def _publish(self, event: object) -> None:
        if self._publisher is None:
            return
        try:
            await self._publisher.publish(event)  # type: ignore[attr-defined]
        except Exception:
            logger.exception(
                "Failed to publish planner event %s", getattr(event, "event_type", "unknown")
            )
