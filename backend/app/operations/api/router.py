from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.v1.auth import verify_token
from app.operations.api.dependencies import get_operations_runtime
from app.operations.api.schemas import (
    DiagnosticsCollectionResponse,
    HealthOverviewResponse,
    IncidentCollectionResponse,
    MetricsCollectionResponse,
)
from app.operations.core.runtime import OperationsRuntime
from app.operations.infrastructure.db.repositories import (
    SQLAlchemyDiagnosticRepository,
    SQLAlchemyHealthRepository,
    SQLAlchemyIncidentRepository,
    SQLAlchemyMetricsRepository,
)

router = APIRouter(prefix="/operations", tags=["operations"])


@router.get("/health", response_model=HealthOverviewResponse)
async def get_health(
    _: dict = Depends(verify_token),
    runtime: OperationsRuntime = Depends(get_operations_runtime),
) -> HealthOverviewResponse:
    session_factory = runtime.session_factory
    async with session_factory() as session:
        repository = SQLAlchemyHealthRepository(session)
        snapshot = await repository.latest_snapshot()
        return HealthOverviewResponse.from_snapshot(snapshot)


@router.get("/incidents", response_model=IncidentCollectionResponse)
async def get_incidents(
    _: dict = Depends(verify_token),
    runtime: OperationsRuntime = Depends(get_operations_runtime),
) -> IncidentCollectionResponse:
    session_factory = runtime.session_factory
    async with session_factory() as session:
        repository = SQLAlchemyIncidentRepository(session)
        incidents = await repository.list_history()
        return IncidentCollectionResponse.from_domain(incidents)


@router.get("/metrics", response_model=MetricsCollectionResponse)
async def get_metrics(
    _: dict = Depends(verify_token),
    runtime: OperationsRuntime = Depends(get_operations_runtime),
) -> MetricsCollectionResponse:
    session_factory = runtime.session_factory
    async with session_factory() as session:
        repository = SQLAlchemyMetricsRepository(session)
        metrics = await repository.list_recent()
        return MetricsCollectionResponse.from_domain(metrics)


@router.get("/diagnostics", response_model=DiagnosticsCollectionResponse)
async def get_diagnostics(
    _: dict = Depends(verify_token),
    runtime: OperationsRuntime = Depends(get_operations_runtime),
) -> DiagnosticsCollectionResponse:
    session_factory = runtime.session_factory
    async with session_factory() as session:
        repository = SQLAlchemyDiagnosticRepository(session)
        packs = await repository.list_recent()
        return DiagnosticsCollectionResponse.from_domain(packs)
