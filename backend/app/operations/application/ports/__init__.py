from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from app.operations.domain.events import DomainEvent
    from app.operations.domain.models import DiagnosticPack, HealthSnapshot, Incident, MetricSample


@runtime_checkable
class HealthRepository(Protocol):
    async def record_snapshot(self, snapshot: HealthSnapshot) -> HealthSnapshot: ...

    async def list_snapshots(self, limit: int = 100) -> list[HealthSnapshot]: ...

    async def latest_snapshot(self) -> HealthSnapshot | None: ...


@runtime_checkable
class IncidentRepository(Protocol):
    async def create(self, incident: Incident) -> Incident: ...

    async def list_active(self, limit: int = 100) -> list[Incident]: ...

    async def list_history(self, limit: int = 100) -> list[Incident]: ...

    async def get(self, incident_id: str) -> Incident | None: ...

    async def resolve(self, incident_id: str, resolution: str) -> Incident | None: ...


@runtime_checkable
class MetricsRepository(Protocol):
    async def record(self, samples: list[MetricSample]) -> list[MetricSample]: ...

    async def list_recent(self, limit: int = 100) -> list[MetricSample]: ...


@runtime_checkable
class DiagnosticRepository(Protocol):
    async def create(self, pack: DiagnosticPack) -> DiagnosticPack: ...

    async def list_recent(self, limit: int = 100) -> list[DiagnosticPack]: ...

    async def latest(self) -> DiagnosticPack | None: ...


@runtime_checkable
class KnowledgeRepository(Protocol):
    async def list_recent(self, limit: int = 100) -> list[dict[str, str]]: ...


@runtime_checkable
class EventRepository(Protocol):
    async def append(self, event: DomainEvent) -> DomainEvent: ...

    async def list_recent(self, limit: int = 100) -> list[DomainEvent]: ...
