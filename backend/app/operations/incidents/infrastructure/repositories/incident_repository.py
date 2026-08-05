from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from app.operations.incidents.domain.enums import IncidentStatus
from app.operations.incidents.infrastructure.db.models import (
    UaesDiagnosticPackV3,
    UaesIncidentEvidenceV3,
    UaesIncidentV3,
    UaesRootCause,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.operations.incidents.domain.models import (
        DiagnosticPack,
        Incident,
        IncidentEvidence,
        RootCause,
    )

ACTIVE_STATUSES: list[str] = [
    IncidentStatus.DETECTED.value,
    IncidentStatus.INVESTIGATING.value,
    IncidentStatus.EVIDENCE_COLLECTED.value,
    IncidentStatus.ANALYZING.value,
    IncidentStatus.ROOT_CAUSE_FOUND.value,
    IncidentStatus.WAITING_FOR_REPAIR.value,
]


class SQLAlchemyIncidentRepositoryV3:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, incident: Incident) -> None:
        existing = await self.session.get(UaesIncidentV3, incident.incident_id)
        if existing is None:
            self.session.add(UaesIncidentV3.from_domain(incident))
        else:
            existing.timestamp = incident.timestamp
            existing.severity = incident.severity
            existing.component_type = incident.component_type
            existing.component_name = incident.component_name
            existing.environment = incident.environment
            existing.summary = incident.summary
            existing.detailed_description = incident.detailed_description
            existing.status = incident.status
            existing.triggered_by_event = incident.triggered_by_event
            existing.triggered_by_component = incident.triggered_by_component
            existing.triggered_at = incident.triggered_at
            existing.resolution = incident.resolution
            existing.confidence = incident.confidence.value
            existing.recovery_recommendation = incident.recovery_recommendation
            existing.duration_seconds = (
                None if incident.duration is None else incident.duration.total_seconds()
            )
            existing.risk_score = None if incident.risk is None else incident.risk.value
            existing.tags_json = dict(incident.tags)
        await self.session.flush()

    async def get(self, incident_id: str) -> Incident | None:
        entity = await self.session.get(UaesIncidentV3, incident_id)
        return None if entity is None else entity.to_domain()

    async def list_incidents(self, limit: int = 100) -> list[Incident]:
        result = await self.session.execute(
            select(UaesIncidentV3)
            .order_by(UaesIncidentV3.timestamp.desc())
            .limit(limit)
        )
        return [row.to_domain() for row in result.scalars().all()]

    async def find_active(self) -> list[Incident]:
        result = await self.session.execute(
            select(UaesIncidentV3)
            .where(UaesIncidentV3.status.in_(ACTIVE_STATUSES))
            .order_by(UaesIncidentV3.timestamp.desc())
        )
        return [row.to_domain() for row in result.scalars().all()]

    async def find_by_status(self, status: IncidentStatus) -> list[Incident]:
        result = await self.session.execute(
            select(UaesIncidentV3)
            .where(UaesIncidentV3.status == status.value)
            .order_by(UaesIncidentV3.timestamp.desc())
        )
        return [row.to_domain() for row in result.scalars().all()]

    async def find_active_for_component(
        self, component_type: str, component_name: str
    ) -> list[Incident]:
        result = await self.session.execute(
            select(UaesIncidentV3)
            .where(UaesIncidentV3.status.in_(ACTIVE_STATUSES))
            .where(UaesIncidentV3.component_type == component_type)
            .where(UaesIncidentV3.component_name == component_name)
            .order_by(UaesIncidentV3.timestamp.desc())
        )
        return [row.to_domain() for row in result.scalars().all()]

    async def get_evidence(self, incident_id: str) -> list[IncidentEvidence]:
        result = await self.session.execute(
            select(UaesIncidentEvidenceV3)
            .where(UaesIncidentEvidenceV3.incident_id == incident_id)
            .order_by(UaesIncidentEvidenceV3.collected_at)
        )
        return [row.to_domain() for row in result.scalars().all()]

    async def add_evidence(
        self, incident_id: str, evidence: list[IncidentEvidence]
    ) -> None:
        for item in evidence:
            self.session.add(UaesIncidentEvidenceV3.from_domain(item, incident_id))
        await self.session.flush()

    async def get_root_cause(self, incident_id: str) -> RootCause | None:
        result = await self.session.execute(
            select(UaesRootCause)
            .where(UaesRootCause.incident_id == incident_id)
            .order_by(UaesRootCause.determined_at.desc())
            .limit(1)
        )
        row = result.scalars().first()
        return None if row is None else row.to_domain()

    async def add_root_cause(self, incident_id: str, root_cause: RootCause) -> None:
        self.session.add(UaesRootCause.from_domain(root_cause, incident_id))
        await self.session.flush()

    async def get_diagnostic_pack(self, incident_id: str) -> DiagnosticPack | None:
        result = await self.session.execute(
            select(UaesDiagnosticPackV3)
            .where(UaesDiagnosticPackV3.incident_id == incident_id)
            .order_by(UaesDiagnosticPackV3.generated_at.desc())
            .limit(1)
        )
        row = result.scalars().first()
        return None if row is None else row.to_domain()

    async def add_diagnostic_pack(self, incident_id: str, pack: DiagnosticPack) -> None:
        self.session.add(UaesDiagnosticPackV3.from_domain(pack, incident_id))
        await self.session.flush()
