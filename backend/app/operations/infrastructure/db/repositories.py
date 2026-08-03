from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.operations.application.ports import (
    DiagnosticRepository,
    EventRepository,
    HealthRepository,
    IncidentRepository,
    MetricsRepository,
)
from app.operations.domain.enums import IncidentStatus
from app.operations.domain.events import DomainEvent, event_from_dict
from app.operations.domain.models import DiagnosticPack, HealthSnapshot, Incident, MetricSample
from app.operations.infrastructure.db.models import (
    UaesDiagnosticPack,
    UaesEvent,
    UaesHealthSnapshot,
    UaesIncident,
    UaesMetric,
)


class SQLAlchemyHealthRepository(HealthRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record_snapshot(self, snapshot: HealthSnapshot) -> HealthSnapshot:
        entity = UaesHealthSnapshot.from_domain(snapshot)
        self.session.add(entity)
        await self.session.flush()
        return entity.to_domain()

    async def list_snapshots(self, limit: int = 100) -> list[HealthSnapshot]:
        result = await self.session.execute(
            select(UaesHealthSnapshot)
            .options(selectinload(UaesHealthSnapshot.components))
            .order_by(UaesHealthSnapshot.collected_at.desc())
            .limit(limit),
        )
        return [row.to_domain() for row in result.scalars().all()]

    async def latest_snapshot(self) -> HealthSnapshot | None:
        result = await self.session.execute(
            select(UaesHealthSnapshot)
            .options(selectinload(UaesHealthSnapshot.components))
            .order_by(UaesHealthSnapshot.collected_at.desc())
            .limit(1),
        )
        row = result.scalars().first()
        return None if row is None else row.to_domain()


class SQLAlchemyIncidentRepository(IncidentRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, incident: Incident) -> Incident:
        entity = UaesIncident.from_domain(incident)
        self.session.add(entity)
        await self.session.flush()
        return entity.to_domain()

    async def list_active(self, limit: int = 100) -> list[Incident]:
        result = await self.session.execute(
            select(UaesIncident)
            .options(selectinload(UaesIncident.evidence))
            .where(UaesIncident.status.in_(("open", "triaged", "investigating", "escalated")))
            .order_by(UaesIncident.timestamp.desc())
            .limit(limit),
        )
        return [row.to_domain() for row in result.scalars().all()]

    async def list_history(self, limit: int = 100) -> list[Incident]:
        result = await self.session.execute(
            select(UaesIncident)
            .options(selectinload(UaesIncident.evidence))
            .order_by(UaesIncident.timestamp.desc())
            .limit(limit),
        )
        return [row.to_domain() for row in result.scalars().all()]

    async def get(self, incident_id: str) -> Incident | None:
        result = await self.session.execute(
            select(UaesIncident)
            .options(selectinload(UaesIncident.evidence))
            .where(UaesIncident.id == incident_id),
        )
        row = result.scalars().first()
        return None if row is None else row.to_domain()

    async def resolve(self, incident_id: str, resolution: str) -> Incident | None:
        result = await self.session.execute(
            select(UaesIncident)
            .options(selectinload(UaesIncident.evidence))
            .where(UaesIncident.id == incident_id),
        )
        row = result.scalars().first()
        if row is None:
            return None
        row.resolution = resolution
        row.status = IncidentStatus.RESOLVED
        await self.session.flush()
        return row.to_domain()


class SQLAlchemyMetricsRepository(MetricsRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record(self, samples: list[MetricSample]) -> list[MetricSample]:
        entities = [UaesMetric.from_domain(sample) for sample in samples]
        self.session.add_all(entities)
        await self.session.flush()
        return [entity.to_domain() for entity in entities]

    async def list_recent(self, limit: int = 100) -> list[MetricSample]:
        result = await self.session.execute(
            select(UaesMetric).order_by(UaesMetric.observed_at.desc()).limit(limit),
        )
        return [row.to_domain() for row in result.scalars().all()]


class SQLAlchemyDiagnosticRepository(DiagnosticRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, pack: DiagnosticPack) -> DiagnosticPack:
        entity = UaesDiagnosticPack.from_domain(pack)
        self.session.add(entity)
        await self.session.flush()
        return entity.to_domain()

    async def list_recent(self, limit: int = 100) -> list[DiagnosticPack]:
        result = await self.session.execute(
            select(UaesDiagnosticPack)
            .order_by(UaesDiagnosticPack.generated_at.desc())
            .limit(limit),
        )
        return [row.to_domain() for row in result.scalars().all()]

    async def latest(self) -> DiagnosticPack | None:
        result = await self.session.execute(
            select(UaesDiagnosticPack).order_by(UaesDiagnosticPack.generated_at.desc()).limit(1),
        )
        row = result.scalars().first()
        return None if row is None else row.to_domain()


class SQLAlchemyEventRepository(EventRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def append(self, event: DomainEvent) -> DomainEvent:
        payload = event.to_dict()
        aggregate_id = (
            payload.get("incident_id")
            or payload.get("snapshot_id")
            or payload.get("pack_id")
            or event.event_id
        )
        entity = UaesEvent(
            event_type=event.event_type,
            aggregate_type=event.__class__.__name__,
            aggregate_id=str(aggregate_id),
            occurred_at=event.occurred_at,
            correlation_id=event.correlation_id,
            causation_id=event.causation_id,
            source=event.source,
            payload_json=payload,
            metadata_json={"event_class": event.__class__.__name__},
        )
        self.session.add(entity)
        await self.session.flush()
        return event

    async def list_recent(self, limit: int = 100) -> list[DomainEvent]:
        result = await self.session.execute(
            select(UaesEvent).order_by(UaesEvent.occurred_at.desc()).limit(limit),
        )
        return [event_from_dict(row.payload_json) for row in result.scalars().all()]
