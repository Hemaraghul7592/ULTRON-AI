from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.auth import verify_token
from app.operations.api.dependencies import get_operations_runtime
from app.operations.core.runtime import OperationsRuntime  # noqa: TC001
from app.operations.planner.api.schemas import (
    GeneratePlanRequest,
    PlanDetailResponse,
    PlanListResponse,
    RepairCandidateResponse,
    RepairPlanResponse,
    SimulationResultResponse,
    StrategyListResponse,
    StrategySummaryResponse,
)
from app.operations.planner.domain.strategies import get_all_strategies
from app.operations.planner.infrastructure.repositories import SQLAlchemyPlanRepository

router = APIRouter(prefix="/planner", tags=["planner"])


@router.get("/plans", response_model=PlanListResponse)
async def list_plans(
    limit: int = 100,
    _: dict = Depends(verify_token),  # noqa: B008
    runtime: OperationsRuntime = Depends(get_operations_runtime),  # noqa: B008
) -> PlanListResponse:
    async with runtime.session_factory() as session:
        repository = SQLAlchemyPlanRepository(session)
        plans = await repository.list_plans(limit=limit)
        return PlanListResponse(
            plans=[RepairPlanResponse.from_domain(p) for p in plans],
            count=len(plans),
        )


@router.get("/plans/{plan_id}", response_model=PlanDetailResponse)
async def get_plan(
    plan_id: str,
    _: dict = Depends(verify_token),  # noqa: B008
    runtime: OperationsRuntime = Depends(get_operations_runtime),  # noqa: B008
) -> PlanDetailResponse:
    async with runtime.session_factory() as session:
        repository = SQLAlchemyPlanRepository(session)
        plan = await repository.get(plan_id)
        if plan is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan not found",
            )
        candidates = [RepairCandidateResponse.from_domain(c) for c in plan.candidates]
        simulation = (
            SimulationResultResponse.from_domain(plan.simulation_result)
            if plan.simulation_result
            else None
        )
        return PlanDetailResponse(
            plan=RepairPlanResponse.from_domain(plan),
            candidates=candidates,
            simulation=simulation,
        )


@router.post("/generate", response_model=PlanDetailResponse)
async def generate_plan(
    request: GeneratePlanRequest,
    _: dict = Depends(verify_token),  # noqa: B008
    runtime: OperationsRuntime = Depends(get_operations_runtime),  # noqa: B008
) -> PlanDetailResponse:
    async with runtime.session_factory() as session:
        from app.operations.incidents.infrastructure.repositories import (
            SQLAlchemyIncidentRepositoryV3,
        )
        from app.operations.planner.application.knowledge_adapter import KnowledgeAdapter
        from app.operations.planner.application.planning_service import (
            RepairPlanningService,
        )
        from app.operations.planner.application.publisher import InMemoryPlannerPublisher
        from app.operations.planner.application.simulation_service import SimulationService
        from app.operations.planner.domain.confidence_model import ConfidenceAnalyzer
        from app.operations.planner.domain.constraint_model import ConstraintEngine
        from app.operations.planner.domain.cost_model import CostEstimator
        from app.operations.planner.domain.risk_model import RiskAnalyzer
        from app.operations.planner.domain.rollback_planner import RollbackPlanner
        from app.operations.planner.domain.validation_planner import ValidationPlanner

        inc_repo = SQLAlchemyIncidentRepositoryV3(session)
        incident = await inc_repo.get(request.incident_id)
        if incident is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Incident not found",
            )

        root_cause = await inc_repo.get_root_cause(request.incident_id)
        if root_cause is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No root cause found for this incident",
            )

        evidence = await inc_repo.get_evidence(request.incident_id)
        evidence_categories = {e.category.value for e in evidence}
        has_health = any(e.category.value == "system" for e in evidence)
        has_metrics = any(e.category.value == "metric" for e in evidence)
        has_logs = any(e.category.value == "log" for e in evidence)

        plan_repo = SQLAlchemyPlanRepository(session)

        class _StrategyProvider:
            def get_all_strategies(self) -> list:  # type: ignore[override]
                return get_all_strategies()

            def get_strategies_for_category(self, category: str) -> list:  # type: ignore[override]
                from app.operations.incidents.domain.enums import RootCauseCategory
                from app.operations.planner.domain.strategies import get_strategies_for_category

                return get_strategies_for_category(RootCauseCategory(category))

        service = RepairPlanningService(
            repository=plan_repo,
            strategy_provider=_StrategyProvider(),  # type: ignore[arg-type]
            risk_analyzer=RiskAnalyzer(),  # type: ignore[arg-type]
            confidence_analyzer=ConfidenceAnalyzer(),  # type: ignore[arg-type]
            cost_estimator=CostEstimator(),  # type: ignore[arg-type]
            constraint_engine=ConstraintEngine(),  # type: ignore[arg-type]
            knowledge_adapter=KnowledgeAdapter(),  # type: ignore[arg-type]
            simulation_engine=SimulationService(),  # type: ignore[arg-type]
            rollback_planner=RollbackPlanner(),  # type: ignore[arg-type]
            validation_pipeline=ValidationPlanner(),  # type: ignore[arg-type]
            approval_policy=None,
            publisher=InMemoryPlannerPublisher(),
        )

        plan = await service.plan(
            incident_id=request.incident_id,
            root_cause=root_cause,
            incident=incident,
            evidence_categories=evidence_categories,
            has_health_check=has_health,
            has_metrics=has_metrics,
            has_logs=has_logs,
        )
        await session.commit()

        candidates = [RepairCandidateResponse.from_domain(c) for c in plan.candidates]
        simulation = (
            SimulationResultResponse.from_domain(plan.simulation_result)
            if plan.simulation_result
            else None
        )
        return PlanDetailResponse(
            plan=RepairPlanResponse.from_domain(plan),
            candidates=candidates,
            simulation=simulation,
        )


@router.get("/strategies", response_model=StrategyListResponse)
async def list_strategies(
    _: dict = Depends(verify_token),  # noqa: B008
) -> StrategyListResponse:
    strategies = get_all_strategies()
    items = [
        StrategySummaryResponse(
            id=s.id,
            name=s.name,
            repair_type=s.repair_type.value
            if hasattr(s.repair_type, "value")
            else str(s.repair_type),
            root_cause_categories=[rc.value for rc in s.root_cause_categories],
            estimated_duration_seconds=s.estimated_duration_seconds,
        )
        for s in strategies
    ]
    return StrategyListResponse(strategies=items, count=len(items))


@router.get("/history", response_model=PlanListResponse)
async def list_history(
    limit: int = 100,
    _: dict = Depends(verify_token),  # noqa: B008
    runtime: OperationsRuntime = Depends(get_operations_runtime),  # noqa: B008
) -> PlanListResponse:
    async with runtime.session_factory() as session:
        repository = SQLAlchemyPlanRepository(session)
        plans = await repository.list_history(limit=limit)
        return PlanListResponse(
            plans=[RepairPlanResponse.from_domain(p) for p in plans],
            count=len(plans),
        )
