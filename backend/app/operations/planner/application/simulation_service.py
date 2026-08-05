from __future__ import annotations

import time

from app.operations.planner.domain.enums import SimulationOutcome
from app.operations.planner.domain.models import (
    CandidateSimulation,
    RepairCandidate,
    SimulationResult,
)


class SimulationService:
    def simulate(
        self,
        candidate: RepairCandidate,
        environment: str,
        risk_score: float,
    ) -> CandidateSimulation:
        warnings: list[str] = []
        errors: list[str] = []

        preconditions_met = True
        if environment == "production" and risk_score > 80:
            preconditions_met = False
            warnings.append("High risk in production — preconditions not fully met")

        if candidate.estimated_duration_seconds > 600:
            warnings.append("Long estimated duration — may impact service availability")

        outcome = self._determine_outcome(preconditions_met, risk_score, candidate)

        risk_change = 0.0
        if outcome == SimulationOutcome.SUCCESS:
            risk_change = -5.0
        elif outcome == SimulationOutcome.FAILURE:
            risk_change = 15.0
        elif outcome == SimulationOutcome.PARTIAL_SUCCESS:
            risk_change = 5.0

        confidence_change = 0.0
        if outcome == SimulationOutcome.SUCCESS:
            confidence_change = 0.1
        elif outcome == SimulationOutcome.FAILURE:
            confidence_change = -0.2

        return CandidateSimulation(
            candidate_id=candidate.candidate_id,
            plan_id=candidate.plan_id,
            outcome=outcome,
            expected_risk_change=risk_change,
            expected_confidence_change=confidence_change,
            preconditions_met=preconditions_met,
            postconditions_met=outcome in (SimulationOutcome.SUCCESS, SimulationOutcome.NO_IMPACT),
            simulated_duration_seconds=candidate.estimated_duration_seconds,
            simulated_resource_impact={
                "cpu_percent": 10.0 if risk_score < 50 else 25.0,
                "memory_mb": 50.0,
            },
            warnings=warnings,
            errors=errors,
        )

    def simulate_all(
        self,
        candidates: list[RepairCandidate],
        environment: str,
        risk_scores: dict[str, float],
    ) -> SimulationResult:
        start = time.perf_counter()
        simulations: list[CandidateSimulation] = []

        for candidate in candidates:
            risk = risk_scores.get(candidate.candidate_id, 50.0)
            sim = self.simulate(candidate, environment, risk)
            simulations.append(sim)

        duration_ms = int((time.perf_counter() - start) * 1000)

        recommended = None
        for sim in simulations:
            if sim.outcome == SimulationOutcome.SUCCESS:
                recommended = sim.candidate_id
                break

        overall = SimulationOutcome.UNKNOWN
        if simulations:
            outcomes = [s.outcome for s in simulations]
            if all(o == SimulationOutcome.SUCCESS for o in outcomes):
                overall = SimulationOutcome.SUCCESS
            elif any(o == SimulationOutcome.FAILURE for o in outcomes):
                overall = SimulationOutcome.PARTIAL_SUCCESS
            elif any(o == SimulationOutcome.SUCCESS for o in outcomes):
                overall = SimulationOutcome.SUCCESS
            else:
                overall = SimulationOutcome.NO_IMPACT

        return SimulationResult(
            plan_id=candidates[0].plan_id if candidates else "",
            candidate_simulations=simulations,
            recommended_candidate_id=recommended,
            simulation_duration_ms=duration_ms,
            overall_outcome=overall,
        )

    def _determine_outcome(
        self,
        preconditions_met: bool,
        risk_score: float,
        candidate: RepairCandidate,
    ) -> SimulationOutcome:
        if not preconditions_met:
            return SimulationOutcome.FAILURE
        if risk_score > 90:
            return SimulationOutcome.FAILURE
        if risk_score > 70:
            return SimulationOutcome.PARTIAL_SUCCESS
        if candidate.estimated_duration_seconds == 0:
            return SimulationOutcome.NO_IMPACT
        return SimulationOutcome.SUCCESS
