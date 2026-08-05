from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.operations.planner.domain.models import (
    RepairCandidate,
)

if TYPE_CHECKING:
    from app.operations.planner.domain.models import (
        KnowledgeSnapshot,
    )
    from app.operations.planner.domain.strategies import RepairStrategy

logger = logging.getLogger(__name__)


class StrategySelector:
    def select(
        self,
        strategies: list[RepairStrategy],
        root_cause_category: str,
        environment: str,
        severity: str,
        knowledge_snapshot: KnowledgeSnapshot | None = None,
    ) -> list[RepairCandidate]:
        candidates: list[RepairCandidate] = []

        for strategy in strategies:
            if not self._matches_category(strategy, root_cause_category):
                continue
            if not self._matches_environment(strategy, environment):
                continue
            if not self._matches_severity(strategy, severity):
                continue

            candidate = self._build_candidate(strategy)
            candidates.append(candidate)

        return candidates

    def _matches_category(self, strategy: RepairStrategy, root_cause_category: str) -> bool:
        return root_cause_category in strategy.root_cause_categories

    def _matches_environment(self, strategy: RepairStrategy, environment: str) -> bool:
        return environment in strategy.environments

    def _matches_severity(self, strategy: RepairStrategy, severity: str) -> bool:
        severity_order = {"info": 0, "warning": 1, "high": 2, "critical": 3, "emergency": 4}
        min_level = severity_order.get(strategy.severity_minimum, 0)
        current_level = severity_order.get(severity, 0)
        return current_level >= min_level

    def _build_candidate(self, strategy: RepairStrategy) -> RepairCandidate:
        return RepairCandidate(
            plan_id="",
            repair_type=strategy.repair_type,
            strategy_id=strategy.id,
            strategy_name=strategy.name,
            description=strategy.description,
            estimated_duration_seconds=strategy.estimated_duration_seconds,
            prerequisites=list(strategy.prerequisites),
            affected_components=list(strategy.affected_components),
        )
