from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.operations.planner.domain.models import (
    KnowledgeSnapshot,
)

if TYPE_CHECKING:
    from app.operations.planner.application.ports import KnowledgeRepositoryPort

logger = logging.getLogger(__name__)


class KnowledgeAdapter:
    def __init__(self, repository: KnowledgeRepositoryPort | None = None) -> None:
        self._repository = repository

    async def consult(
        self,
        incident_id: str,
        root_cause_category: str,
        component_type: str,
        environment: str,
    ) -> KnowledgeSnapshot:
        if self._repository is None:
            return self._empty_snapshot(incident_id, root_cause_category)

        try:
            similar = await self._repository.find_similar(
                root_cause_category=root_cause_category,
                component_type=component_type,
                environment=environment,
            )
            success_rates: dict[str, float] = {}
            avg_durations: dict[str, int] = {}

            strategy_ids: set[str] = set()
            for s in similar:
                strategy_ids.add(s.strategy_used)

            for sid in strategy_ids:
                success_rates[sid] = await self._repository.get_success_rate(
                    sid, root_cause_category
                )
                avg_durations[sid] = await self._repository.get_average_duration(
                    sid, root_cause_category
                )

            return KnowledgeSnapshot(
                incident_id=incident_id,
                root_cause_category=root_cause_category,
                similar_incidents=similar,
                historical_success_rates=success_rates,
                historical_avg_duration=avg_durations,
            )
        except Exception:
            logger.exception("Knowledge consultation failed for incident %s", incident_id)
            return self._empty_snapshot(incident_id, root_cause_category)

    def _empty_snapshot(self, incident_id: str, root_cause_category: str) -> KnowledgeSnapshot:
        return KnowledgeSnapshot(
            incident_id=incident_id,
            root_cause_category=root_cause_category,
            similar_incidents=[],
            historical_success_rates={},
            historical_avg_duration={},
        )
