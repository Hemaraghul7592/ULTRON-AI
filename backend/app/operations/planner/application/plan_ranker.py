from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.operations.planner.domain.models import (
        KnowledgeSnapshot,
        RepairCandidate,
        RepairCost,
    )


class PlanRanker:
    WEIGHTS = {
        "risk": 0.25,
        "confidence": 0.20,
        "speed": 0.15,
        "impact": 0.10,
        "historical": 0.10,
        "cost": 0.10,
        "constraint": 0.05,
        "simulation": 0.05,
    }

    def rank(
        self,
        candidates: list[RepairCandidate],
        knowledge_snapshot: KnowledgeSnapshot | None = None,
    ) -> list[RepairCandidate]:
        scored: list[tuple[float, dict[str, float], RepairCandidate]] = []

        for c in candidates:
            scores = {
                "risk": self._risk_score(c.risk.score if c.risk else 50.0),
                "confidence": self._confidence_score(
                    c.confidence.overall_score if c.confidence else 0.5
                ),
                "speed": self._speed_score(c.estimated_duration_seconds),
                "impact": self._impact_score(c.affected_components),
                "historical": self._historical_score(
                    c.strategy_id,
                    c.strategy_name,
                    knowledge_snapshot,
                ),
                "cost": self._cost_score(c.cost),
                "constraint": self._constraint_score(c.constraints),
                "simulation": self._simulation_score(c.simulation),
            }
            composite = sum(scores[k] * self.WEIGHTS[k] for k in self.WEIGHTS)
            scored.append((composite, scores, c))

        scored.sort(key=lambda x: x[0], reverse=True)
        result: list[RepairCandidate] = []
        for rank_pos, (score, _, candidate) in enumerate(scored, 1):
            updated = candidate.model_copy(update={"score": round(score, 4), "rank": rank_pos})
            result.append(updated)

        return result

    def _risk_score(self, risk_score: float) -> float:
        return max(0.0, (100 - risk_score) / 100)

    def _confidence_score(self, confidence: float) -> float:
        return confidence

    def _speed_score(self, duration: int) -> float:
        return max(0.0, 1 - duration / 3600)

    def _impact_score(self, affected: list[str]) -> float:
        return max(0.0, 1 - len(affected) / 5)

    def _historical_score(
        self,
        strategy_id: str,
        strategy_name: str,
        knowledge: KnowledgeSnapshot | None,
    ) -> float:
        if knowledge and strategy_id in knowledge.historical_success_rates:
            return knowledge.historical_success_rates[strategy_id]
        return 0.5

    def _cost_score(self, cost: RepairCost | None) -> float:
        if cost is None:
            return 0.5
        return max(0.0, (100 - cost.operational_cost) / 100)

    def _constraint_score(self, constraints: list) -> float:
        if not constraints:
            return 1.0
        hard = [c for c in constraints if c.severity == "hard"]
        if not hard:
            return 1.0
        return 0.8

    def _simulation_score(self, simulation: object | None) -> float:
        if simulation is None:
            return 0.5
        outcome = getattr(simulation, "outcome", "unknown")
        return {
            "success": 1.0,
            "partial_success": 0.6,
            "failure": 0.0,
            "no_impact": 0.8,
            "unknown": 0.5,
        }.get(str(outcome), 0.5)
