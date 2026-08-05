from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from app.operations.incidents.domain.enums import IncidentStatus
    from app.operations.incidents.domain.events import IncidentDomainEvent
    from app.operations.incidents.domain.models import (
        DiagnosticPack,
        EvidenceBundle,
        Incident,
        IncidentEvidence,
        RecoveryRecommendation,
        RootCause,
    )


@runtime_checkable
class IncidentRepository(Protocol):
    async def save(self, incident: Incident) -> None: ...

    async def get(self, incident_id: str) -> Incident | None: ...

    async def list_incidents(self, limit: int = 100) -> list[Incident]: ...

    async def find_active(self) -> list[Incident]: ...

    async def find_by_status(self, status: IncidentStatus) -> list[Incident]: ...

    async def find_active_for_component(
        self, component_type: str, component_name: str
    ) -> list[Incident]: ...

    async def get_evidence(self, incident_id: str) -> list[IncidentEvidence]: ...

    async def add_evidence(
        self, incident_id: str, evidence: list[IncidentEvidence]
    ) -> None: ...

    async def get_root_cause(self, incident_id: str) -> RootCause | None: ...

    async def add_root_cause(self, incident_id: str, root_cause: RootCause) -> None: ...

    async def get_diagnostic_pack(self, incident_id: str) -> DiagnosticPack | None: ...

    async def add_diagnostic_pack(self, incident_id: str, pack: DiagnosticPack) -> None: ...


@runtime_checkable
class EvidenceCollectorPort(Protocol):
    async def collect_evidence(self, incident: Incident) -> EvidenceBundle: ...


@runtime_checkable
class RootCauseAnalysisPort(Protocol):
    def analyze(self, incident: Incident, evidence_bundle: EvidenceBundle) -> RootCause: ...

    def recommend_recovery(self, root_cause: RootCause) -> RecoveryRecommendation: ...


@runtime_checkable
class DiagnosticPackPort(Protocol):
    def generate(
        self,
        incident: Incident,
        evidence_bundle: EvidenceBundle,
        root_cause: RootCause,
        recovery_recommendation: RecoveryRecommendation,
    ) -> DiagnosticPack: ...


@runtime_checkable
class InvestigationPublisher(Protocol):
    async def publish(self, event: IncidentDomainEvent) -> None: ...
