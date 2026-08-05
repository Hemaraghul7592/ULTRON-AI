from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from app.operations.planner.domain.enums import RepairStatus
    from app.operations.planner.domain.events import PlannerDomainEvent
    from app.operations.planner.domain.models import (
        CandidateSimulation,
        ConfidenceDimensions,
        RepairArtifact,
        RepairCandidate,
        RepairConstraint,
        RepairCost,
        RepairLearningEvent,
        RepairPlan,
        RepairRisk,
        RepairStrategy,
        RollbackPlan,
        RollbackReadinessCheck,
        SimilarIncident,
        ValidationPipelineResult,
    )


@runtime_checkable
class PlanRepository(Protocol):
    async def save(self, plan: RepairPlan) -> None: ...
    async def get(self, plan_id: str) -> RepairPlan | None: ...
    async def get_by_incident(self, incident_id: str) -> RepairPlan | None: ...
    async def list_plans(self, limit: int = 100) -> list[RepairPlan]: ...
    async def list_by_status(self, status: RepairStatus, limit: int = 100) -> list[RepairPlan]: ...
    async def list_history(self, limit: int = 100) -> list[RepairPlan]: ...
    async def update_status(self, plan_id: str, status: RepairStatus) -> None: ...
    async def save_artifact(self, artifact: RepairArtifact) -> None: ...
    async def get_artifact(self, plan_id: str) -> RepairArtifact | None: ...
    async def list_artifacts(self, limit: int = 100) -> list[RepairArtifact]: ...


@runtime_checkable
class RepairStrategyProvider(Protocol):
    def get_all_strategies(self) -> list[RepairStrategy]: ...
    def get_strategies_for_category(self, category: str) -> list[RepairStrategy]: ...


@runtime_checkable
class RiskAnalyzerPort(Protocol):
    def analyze(
        self,
        candidate: RepairCandidate,
        component_type: str,
        environment: str,
        root_cause_category: str,
        root_cause_confidence: float,
    ) -> RepairRisk: ...


@runtime_checkable
class ConfidenceAnalyzerPort(Protocol):
    def analyze(
        self,
        candidate: RepairCandidate,
        root_cause_confidence: float,
        evidence_categories: set[str],
        has_health_check: bool,
        has_metrics: bool,
        has_logs: bool,
        environment: str,
    ) -> ConfidenceDimensions: ...


@runtime_checkable
class CostEstimatorPort(Protocol):
    def estimate(
        self,
        repair_type: str,
        estimated_duration_seconds: int,
        affected_components: list[str],
    ) -> RepairCost: ...


@runtime_checkable
class ConstraintEnginePort(Protocol):
    def evaluate(
        self,
        component_type: str,
        environment: str,
        severity: str,
    ) -> list[RepairConstraint]: ...

    def satisfies(
        self,
        candidate: RepairCandidate,
        constraints: list[RepairConstraint],
    ) -> tuple[bool, list[str]]: ...


@runtime_checkable
class KnowledgeRepositoryPort(Protocol):
    async def find_similar(
        self,
        root_cause_category: str,
        component_type: str,
        environment: str,
        limit: int = 10,
    ) -> list[SimilarIncident]: ...

    async def get_success_rate(
        self,
        strategy_id: str,
        root_cause_category: str,
    ) -> float: ...

    async def get_average_duration(
        self,
        strategy_id: str,
        root_cause_category: str,
    ) -> int: ...

    async def record_outcome(self, event: RepairLearningEvent) -> None: ...


@runtime_checkable
class SimulationEnginePort(Protocol):
    def simulate(
        self,
        candidate: RepairCandidate,
        environment: str,
        risk_score: float,
    ) -> CandidateSimulation: ...


@runtime_checkable
class ValidationPipelinePort(Protocol):
    def generate_pre_approval_checks(
        self,
        plan: RepairPlan,
    ) -> ValidationPipelineResult: ...

    def check_rollback_readiness(
        self,
        plan: RepairPlan,
    ) -> RollbackReadinessCheck: ...


@runtime_checkable
class ApprovalPolicyPort(Protocol):
    def determine_level(
        self,
        risk_level: str,
        confidence_score: float,
        environment: str,
    ) -> str: ...


@runtime_checkable
class RollbackPlannerPort(Protocol):
    def generate(
        self,
        candidate: RepairCandidate,
        plan_id: str,
    ) -> RollbackPlan: ...


@runtime_checkable
class PlannerEventPublisher(Protocol):
    async def publish(self, event: PlannerDomainEvent) -> None: ...
