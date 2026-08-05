from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Protocol, runtime_checkable
from uuid import uuid4

from app.operations.incidents.domain.enums import EvidenceCategory
from app.operations.incidents.domain.models import IncidentEvidence

if TYPE_CHECKING:
    from app.operations.incidents.domain.models import Incident


@runtime_checkable
class EvidenceCollector(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def category(self) -> EvidenceCategory: ...

    async def collect(self, incident: Incident) -> IncidentEvidence: ...

    async def collect_error(self, incident: Incident, error: str) -> IncidentEvidence: ...


def _make_evidence_id() -> str:
    return str(uuid4())


def _make_checksum(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()[:32]


def _make_excerpt(text: str, max_len: int = 2000) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len] + "...(truncated)"


def _build_evidence(
    incident: Incident,
    category: EvidenceCategory,
    source: str,
    payload_ref: str,
    content: str,
    metadata: dict[str, str] | None = None,
) -> IncidentEvidence:
    return IncidentEvidence(
        evidence_id=_make_evidence_id(),
        incident_id=incident.incident_id,
        category=category,
        source=source,
        collected_at=datetime.now(UTC),
        payload_ref=payload_ref,
        redacted_excerpt=_make_excerpt(content),
        checksum=_make_checksum(content),
        metadata=metadata or {},
    )


def _build_error_evidence(
    incident: Incident,
    collector_name: str,
    error: str,
    metadata: dict[str, str] | None = None,
) -> IncidentEvidence:
    return IncidentEvidence(
        evidence_id=_make_evidence_id(),
        incident_id=incident.incident_id,
        category=EvidenceCategory.SYSTEM,
        source=collector_name,
        collected_at=datetime.now(UTC),
        payload_ref="error",
        redacted_excerpt=f"Collection failed: {error}",
        checksum=_make_checksum(f"{collector_name}:{error}"),
        metadata={**(metadata or {}), "error_type": type(error).__name__},
    )


class BaseCollector:
    name: str = "base"
    category: EvidenceCategory = EvidenceCategory.SYSTEM

    async def collect(self, incident: Incident) -> IncidentEvidence:
        raise NotImplementedError

    async def collect_error(self, incident: Incident, error: str) -> IncidentEvidence:
        return _build_error_evidence(incident, self.name, error)

    def _safe_build(
        self,
        incident: Incident,
        source: str,
        payload_ref: str,
        content: str,
        metadata: dict[str, str] | None = None,
    ) -> IncidentEvidence:
        return _build_evidence(
            incident=incident,
            category=self.category,
            source=source,
            payload_ref=payload_ref,
            content=content,
            metadata=metadata,
        )
