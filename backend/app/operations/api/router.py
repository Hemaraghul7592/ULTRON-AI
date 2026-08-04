from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.auth import verify_token
from app.operations.api.dependencies import get_operations_runtime
from app.operations.api.schemas import (
    ComponentHistoryResponse,
    DiagnosticsCollectionResponse,
    HealthOverviewResponse,
    IncidentCollectionResponse,
    MetricsCollectionResponse,
)
from app.operations.core.runtime import OperationsRuntime  # noqa: TC001
from app.operations.infrastructure.db.repositories import (
    SQLAlchemyDiagnosticRepository,
    SQLAlchemyHealthRepository,
    SQLAlchemyIncidentRepository,
    SQLAlchemyMetricsRepository,
)

router = APIRouter(prefix="/operations", tags=["operations"])


def _get_aggregator(runtime: OperationsRuntime):
    if runtime.health_aggregator is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Health aggregator not initialized",
        )
    return runtime.health_aggregator


def _get_scheduler(runtime: OperationsRuntime):
    if runtime.monitoring_scheduler is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Monitoring scheduler not initialized",
        )
    return runtime.monitoring_scheduler


@router.get("/health", response_model=HealthOverviewResponse)
async def get_health(
    _: dict = Depends(verify_token),  # noqa: B008
    runtime: OperationsRuntime = Depends(get_operations_runtime),  # noqa: B008
) -> HealthOverviewResponse:
    session_factory = runtime.session_factory
    async with session_factory() as session:
        repository = SQLAlchemyHealthRepository(session)
        snapshot = await repository.latest_snapshot()
        return HealthOverviewResponse.from_snapshot(snapshot)


@router.get("/health/live", response_model=HealthOverviewResponse)
async def get_live_health(
    _: dict = Depends(verify_token),  # noqa: B008
    runtime: OperationsRuntime = Depends(get_operations_runtime),  # noqa: B008
) -> HealthOverviewResponse:
    aggregator = _get_aggregator(runtime)
    snapshot = await aggregator.collect()
    session_factory = runtime.session_factory
    async with session_factory() as session:
        repository = SQLAlchemyHealthRepository(session)
        await repository.record_snapshot(snapshot)
    return HealthOverviewResponse.from_snapshot(snapshot)


@router.post("/health/trigger", response_model=HealthOverviewResponse)
async def trigger_health_check(
    _: dict = Depends(verify_token),  # noqa: B008
    runtime: OperationsRuntime = Depends(get_operations_runtime),  # noqa: B008
) -> HealthOverviewResponse:
    aggregator = _get_aggregator(runtime)
    snapshot = await aggregator.collect()
    session_factory = runtime.session_factory
    async with session_factory() as session:
        repository = SQLAlchemyHealthRepository(session)
        await repository.record_snapshot(snapshot)
    return HealthOverviewResponse.from_snapshot(snapshot)


@router.get(
    "/components/{component_type}/{component_name}/history",
    response_model=ComponentHistoryResponse,
)
async def get_component_history(
    component_type: str,
    component_name: str,
    _: dict = Depends(verify_token),  # noqa: B008
    runtime: OperationsRuntime = Depends(get_operations_runtime),  # noqa: B008
) -> ComponentHistoryResponse:
    from app.operations.domain.enums import ComponentType

    try:
        component_type_enum = ComponentType(component_type)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid component type: {component_type}",
        ) from exc

    session_factory = runtime.session_factory
    async with session_factory() as session:
        repository = SQLAlchemyHealthRepository(session)
        snapshots = await repository.snapshots_by_component(component_type_enum, component_name)
        return ComponentHistoryResponse.from_domain(snapshots)


@router.get("/incidents", response_model=IncidentCollectionResponse)
async def get_incidents(
    _: dict = Depends(verify_token),  # noqa: B008
    runtime: OperationsRuntime = Depends(get_operations_runtime),  # noqa: B008
) -> IncidentCollectionResponse:
    session_factory = runtime.session_factory
    async with session_factory() as session:
        repository = SQLAlchemyIncidentRepository(session)
        incidents = await repository.list_history()
        return IncidentCollectionResponse.from_domain(incidents)


@router.get("/metrics", response_model=MetricsCollectionResponse)
async def get_metrics(
    _: dict = Depends(verify_token),  # noqa: B008
    runtime: OperationsRuntime = Depends(get_operations_runtime),  # noqa: B008
) -> MetricsCollectionResponse:
    session_factory = runtime.session_factory
    async with session_factory() as session:
        repository = SQLAlchemyMetricsRepository(session)
        metrics = await repository.list_recent()
        return MetricsCollectionResponse.from_domain(metrics)


@router.get("/diagnostics", response_model=DiagnosticsCollectionResponse)
async def get_diagnostics(
    _: dict = Depends(verify_token),  # noqa: B008
    runtime: OperationsRuntime = Depends(get_operations_runtime),  # noqa: B008
) -> DiagnosticsCollectionResponse:
    session_factory = runtime.session_factory
    async with session_factory() as session:
        repository = SQLAlchemyDiagnosticRepository(session)
        packs = await repository.list_recent()
        return DiagnosticsCollectionResponse.from_domain(packs)
