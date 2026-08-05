from __future__ import annotations

import asyncio
import logging
import time
from typing import TYPE_CHECKING

from app.operations.incidents.domain.models import EvidenceBundle

if TYPE_CHECKING:
    from app.operations.incidents.domain.models import Incident, IncidentEvidence
    from app.operations.incidents.infrastructure.collectors.base import (
        EvidenceCollector,
    )

logger = logging.getLogger(__name__)


class EvidenceCollectionService:
    def __init__(self, collectors: list[EvidenceCollector]) -> None:
        self._collectors = list(collectors)

    @property
    def collectors(self) -> list[EvidenceCollector]:
        return list(self._collectors)

    def register(self, collector: EvidenceCollector) -> None:
        self._collectors.append(collector)

    async def collect_evidence(self, incident: Incident) -> EvidenceBundle:
        started = time.perf_counter()
        results = await asyncio.gather(
            *(self._collect_one(collector, incident) for collector in self._collectors),
            return_exceptions=False,
        )

        evidence = []
        failed: list[str] = []
        for item in results:
            if item is None:
                continue
            if item.metadata.get("error_type"):
                failed.append(item.source)
            evidence.append(item)

        duration_ms = int((time.perf_counter() - started) * 1000)
        return EvidenceBundle(
            incident_id=incident.incident_id,
            evidence=evidence,
            collection_duration_ms=duration_ms,
            failed_collectors=failed,
        )

    async def _collect_one(
        self, collector: EvidenceCollector, incident: Incident
    ) -> IncidentEvidence | None:
        try:
            return await collector.collect(incident)
        except Exception as exc:
            logger.exception("Collector %s failed", collector.name)
            try:
                return await collector.collect_error(incident, str(exc))
            except Exception:
                logger.exception("Collector %s error handler also failed", collector.name)
                return None
