from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import uuid4

from app.operations.domain.enums import (
    ComponentType,
    EnvironmentType,
    HealthStatus,
)
from app.operations.domain.value_objects import utc_now

if TYPE_CHECKING:
    from app.operations.domain.models import ComponentHealth, HealthSnapshot
    from app.operations.monitoring.interface import Monitor


STATUS_WEIGHTS: dict[HealthStatus, float] = {
    HealthStatus.HEALTHY: 1.0,
    HealthStatus.WARNING: 0.5,
    HealthStatus.CRITICAL: 0.0,
    HealthStatus.OFFLINE: 0.0,
    HealthStatus.NOT_CONFIGURED: 0.5,
}

WORST_STATUS_ORDER: list[HealthStatus] = [
    HealthStatus.CRITICAL,
    HealthStatus.OFFLINE,
    HealthStatus.WARNING,
    HealthStatus.NOT_CONFIGURED,
    HealthStatus.HEALTHY,
]

WORST_STATUS_RANK: dict[HealthStatus, int] = {s: i for i, s in enumerate(WORST_STATUS_ORDER)}


def _worst_status(statuses: list[HealthStatus]) -> HealthStatus:
    non_not_configured = [s for s in statuses if s != HealthStatus.NOT_CONFIGURED]
    if not non_not_configured:
        return HealthStatus.NOT_CONFIGURED
    return min(non_not_configured, key=lambda s: WORST_STATUS_RANK[s])


class HealthAggregator:
    def __init__(self, monitors: list[Monitor]) -> None:
        self._monitors = monitors

    def component_weights(self) -> dict[ComponentType, float]:
        weights: dict[ComponentType, float] = {}
        critical = {
            ComponentType.DATABASE,
            ComponentType.REDIS,
            ComponentType.BACKEND,
        }
        for monitor in self._monitors:
            weights[monitor.component_type] = 2.0 if monitor.component_type in critical else 1.0
        return weights

    async def collect(self) -> HealthSnapshot:
        from app.operations.domain.models import HealthSnapshot

        results: list[ComponentHealth] = []
        for monitor in self._monitors:
            result = await monitor.check()
            results.append(result)

        weights = self.component_weights()
        total_weight = 0.0
        weighted_score_sum = 0.0

        for result in results:
            weight = weights.get(result.component_type, 1.0)
            if result.status == HealthStatus.NOT_CONFIGURED:
                continue
            total_weight += weight
            weighted_score_sum += result.score * weight

        overall_score = round(weighted_score_sum / total_weight, 2) if total_weight > 0 else 0.0

        statuses = [r.status for r in results]
        overall_status = _worst_status(statuses)

        return HealthSnapshot(
            snapshot_id=str(uuid4()),
            environment=results[0].environment if results else EnvironmentType.DEVELOPMENT,
            overall_status=overall_status,
            overall_score=overall_score,
            collected_at=utc_now(),
            components=results,
            source="uaes-monitoring",
        )

    async def latest(self) -> ComponentHealth | None:
        results = await self.collect()
        if not results.components:
            return None
        by_score = sorted(results.components, key=lambda c: c.score, reverse=True)
        return by_score[0]

    def summarize(self, snapshot: HealthSnapshot) -> dict[str, Any]:
        status_counts: dict[str, int] = {
            "healthy": 0,
            "warning": 0,
            "critical": 0,
            "offline": 0,
            "not_configured": 0,
        }
        for comp in snapshot.components:
            status_counts[comp.status] = status_counts.get(comp.status, 0) + 1
        return {
            "overall_status": snapshot.overall_status,
            "overall_score": snapshot.overall_score,
            "total_components": len(snapshot.components),
            "status_breakdown": status_counts,
            "collected_at": snapshot.collected_at.isoformat(),
        }
