from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.auth import verify_token
from app.operations.api.dependencies import get_operations_runtime
from app.operations.core.runtime import OperationsRuntime  # noqa: TC001
from app.operations.incidents.api.schemas import (
    DiagnosticPackResponse,
    EvidenceCollectionResponse,
    IncidentCollectionResponse,
    IncidentDetailResponse,
    IncidentResponse,
    InvestigateRequest,
    InvestigationResponse,
    RecoveryRecommendationResponse,
    RootCauseResponse,
)
from app.operations.incidents.application.diagnostic_pack import DiagnosticPackGenerator
from app.operations.incidents.application.evidence_service import EvidenceCollectionService
from app.operations.incidents.application.investigation_service import InvestigationService
from app.operations.incidents.application.publisher import InMemoryInvestigationPublisher
from app.operations.incidents.domain.analyzer import RootCauseAnalyzer
from app.operations.incidents.infrastructure.collectors import create_default_collectors
from app.operations.incidents.infrastructure.repositories import (
    SQLAlchemyIncidentRepositoryV3,
)

router = APIRouter(prefix="/operations", tags=["operations-incidents"])


@router.get("/incidents", response_model=IncidentCollectionResponse)
async def list_incidents(
    limit: int = 100,
    _: dict = Depends(verify_token),  # noqa: B008
    runtime: OperationsRuntime = Depends(get_operations_runtime),  # noqa: B008
) -> IncidentCollectionResponse:
    async with runtime.session_factory() as session:
        repository = SQLAlchemyIncidentRepositoryV3(session)
        incidents = await repository.list_incidents(limit=limit)
        return IncidentCollectionResponse.from_incidents(incidents)


@router.get("/incidents/active", response_model=IncidentCollectionResponse)
async def list_active_incidents(
    _: dict = Depends(verify_token),  # noqa: B008
    runtime: OperationsRuntime = Depends(get_operations_runtime),  # noqa: B008
) -> IncidentCollectionResponse:
    async with runtime.session_factory() as session:
        repository = SQLAlchemyIncidentRepositoryV3(session)
        incidents = await repository.find_active()
        return IncidentCollectionResponse.from_incidents(incidents)


@router.get("/incidents/history", response_model=IncidentCollectionResponse)
async def list_incident_history(
    limit: int = 100,
    _: dict = Depends(verify_token),  # noqa: B008
    runtime: OperationsRuntime = Depends(get_operations_runtime),  # noqa: B008
) -> IncidentCollectionResponse:
    async with runtime.session_factory() as session:
        repository = SQLAlchemyIncidentRepositoryV3(session)
        incidents = await repository.list_incidents(limit=limit)
        return IncidentCollectionResponse.from_incidents(incidents)


@router.get("/incidents/{incident_id}", response_model=IncidentDetailResponse)
async def get_incident(
    incident_id: str,
    _: dict = Depends(verify_token),  # noqa: B008
    runtime: OperationsRuntime = Depends(get_operations_runtime),  # noqa: B008
) -> IncidentDetailResponse:
    async with runtime.session_factory() as session:
        repository = SQLAlchemyIncidentRepositoryV3(session)
        incident = await repository.get(incident_id)
        if incident is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Incident not found",
            )
        root_cause = await repository.get_root_cause(incident_id)
        pack = await repository.get_diagnostic_pack(incident_id)
        evidence = await repository.get_evidence(incident_id)
        return IncidentDetailResponse(
            incident=IncidentResponse.from_domain(incident),
            root_cause=None if root_cause is None else RootCauseResponse.from_domain(root_cause),
            diagnostic_pack=None if pack is None else DiagnosticPackResponse.from_domain(pack),
            evidence_count=len(evidence),
        )


@router.get(
    "/incidents/{incident_id}/evidence", response_model=EvidenceCollectionResponse
)
async def get_incident_evidence(
    incident_id: str,
    _: dict = Depends(verify_token),  # noqa: B008
    runtime: OperationsRuntime = Depends(get_operations_runtime),  # noqa: B008
) -> EvidenceCollectionResponse:
    async with runtime.session_factory() as session:
        repository = SQLAlchemyIncidentRepositoryV3(session)
        incident = await repository.get(incident_id)
        if incident is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Incident not found",
            )
        evidence = await repository.get_evidence(incident_id)
        return EvidenceCollectionResponse.from_evidence(evidence)


@router.get("/incidents/{incident_id}/diagnostics", response_model=DiagnosticPackResponse)
async def get_incident_diagnostics(
    incident_id: str,
    _: dict = Depends(verify_token),  # noqa: B008
    runtime: OperationsRuntime = Depends(get_operations_runtime),  # noqa: B008
) -> DiagnosticPackResponse:
    async with runtime.session_factory() as session:
        repository = SQLAlchemyIncidentRepositoryV3(session)
        incident = await repository.get(incident_id)
        if incident is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Incident not found",
            )
        pack = await repository.get_diagnostic_pack(incident_id)
        if pack is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Diagnostic pack not found",
            )
        return DiagnosticPackResponse.from_domain(pack)


@router.post("/investigate", response_model=InvestigationResponse)
async def investigate(
    request: InvestigateRequest,
    _: dict = Depends(verify_token),  # noqa: B008
    runtime: OperationsRuntime = Depends(get_operations_runtime),  # noqa: B008
) -> InvestigationResponse:
    async with runtime.session_factory() as session:
        repository = SQLAlchemyIncidentRepositoryV3(session)
        evidence_service = EvidenceCollectionService(collectors=create_default_collectors())
        service = InvestigationService(
            repository=repository,
            evidence_collector=evidence_service,
            root_cause_analyzer=RootCauseAnalyzer(),
            diagnostic_pack_generator=DiagnosticPackGenerator(),
            publisher=InMemoryInvestigationPublisher(),
        )
        trigger = {
            "event_type": "manual_investigation",
            "component_type": request.component_type,
            "component_name": request.component_name,
            "environment": request.environment,
            "status": request.status,
            "message": request.message,
            "source": "api",
        }
        result = await service.investigate(trigger)
        await session.commit()

        return InvestigationResponse(
            incident_id=result.incident_id,
            status=result.status,
            root_cause=None
            if result.root_cause is None
            else RootCauseResponse.from_domain(result.root_cause),
            recovery_recommendation=None
            if result.recovery_recommendation is None
            else RecoveryRecommendationResponse.from_domain(result.recovery_recommendation),
            evidence_count=len(result.evidence_bundle.evidence)
            if result.evidence_bundle
            else 0,
            duration_ms=result.duration_ms,
            errors=list(result.errors),
        )
