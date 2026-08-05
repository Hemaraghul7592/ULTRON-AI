from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from app.operations.planner.domain.models import (
    ApprovalRequirement,
    CandidateSimulation,
    ConfidenceDimensions,
    ExecutionPlan,
    RepairArtifact,
    RepairCandidate,
    RepairConstraint,
    RepairCost,
    RepairGraph,
    RepairPlan,
    RepairRisk,
)
from app.operations.planner.infrastructure.db.models import (
    UaesRepairArtifact,
    UaesRepairCandidate,
    UaesRepairPlan,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.operations.planner.domain.enums import RepairStatus


class SQLAlchemyPlanRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, plan: RepairPlan) -> None:
        existing = await self.session.get(UaesRepairPlan, plan.plan_id)
        plan_data = plan.to_dict()

        if existing is None:
            entity = UaesRepairPlan(
                id=plan.plan_id,
                incident_id=plan.incident_id,
                status=plan.status,
                selected_candidate_id=(
                    plan.selected_candidate.candidate_id if plan.selected_candidate else None
                ),
                environment=plan.environment,
                component_type=plan.component_type,
                component_name=plan.component_name,
                strategy_used=plan.strategy_used,
                planning_duration_ms=plan.planning_duration_ms,
                total_candidates_evaluated=plan.total_candidates_evaluated,
                knowledge_consulted=plan.knowledge_consulted,
                knowledge_snapshot_id=plan.knowledge_snapshot_id,
                created_at=plan.created_at,
                updated_at=plan.updated_at,
                expires_at=plan.expires_at,
                plan_json=plan_data,
                constraints_json=[c.to_dict() for c in plan.constraints],
                approval_json=plan.approval.to_dict() if plan.approval else None,
                execution_json=plan.execution_plan.to_dict() if plan.execution_plan else None,
                simulation_json=plan.simulation_result.to_dict()
                if plan.simulation_result
                else None,
                validation_json=plan.validation.to_dict() if plan.validation else None,
            )
            self.session.add(entity)

            for candidate in plan.candidates:
                cand_entity = UaesRepairCandidate(
                    id=candidate.candidate_id,
                    plan_id=plan.plan_id,
                    repair_type=candidate.repair_type.value,
                    strategy_id=candidate.strategy_id,
                    strategy_name=candidate.strategy_name,
                    description=candidate.description,
                    score=candidate.score,
                    rank=candidate.rank,
                    estimated_duration_seconds=candidate.estimated_duration_seconds,
                    risk_json=candidate.risk.to_dict() if candidate.risk else None,
                    confidence_json=candidate.confidence.to_dict()
                    if candidate.confidence
                    else None,
                    cost_json=candidate.cost.to_dict() if candidate.cost else None,
                    constraints_json=[c.to_dict() for c in candidate.constraints],
                    steps_json=[s.to_dict() for s in candidate.steps],
                    repair_graph_json=candidate.repair_graph.to_dict()
                    if candidate.repair_graph
                    else None,
                    simulation_json=candidate.simulation.to_dict()
                    if candidate.simulation
                    else None,
                    prerequisites_json=list(candidate.prerequisites),
                    affected_components_json=list(candidate.affected_components),
                )
                self.session.add(cand_entity)
        else:
            existing.status = plan.status
            existing.selected_candidate_id = (
                plan.selected_candidate.candidate_id if plan.selected_candidate else None
            )
            existing.strategy_used = plan.strategy_used
            existing.planning_duration_ms = plan.planning_duration_ms
            existing.total_candidates_evaluated = plan.total_candidates_evaluated
            existing.knowledge_consulted = plan.knowledge_consulted
            existing.knowledge_snapshot_id = plan.knowledge_snapshot_id
            existing.updated_at = plan.updated_at
            existing.expires_at = plan.expires_at
            existing.plan_json = plan_data
            existing.constraints_json = [c.to_dict() for c in plan.constraints]
            existing.approval_json = plan.approval.to_dict() if plan.approval else None
            existing.execution_json = plan.execution_plan.to_dict() if plan.execution_plan else None
            existing.simulation_json = (
                plan.simulation_result.to_dict() if plan.simulation_result else None
            )
            existing.validation_json = plan.validation.to_dict() if plan.validation else None

        await self.session.flush()

    async def get(self, plan_id: str) -> RepairPlan | None:
        entity = await self.session.get(UaesRepairPlan, plan_id)
        if entity is None:
            return None
        return self._to_domain(entity)

    async def get_by_incident(self, incident_id: str) -> RepairPlan | None:
        result = await self.session.execute(
            select(UaesRepairPlan)
            .where(UaesRepairPlan.incident_id == incident_id)
            .order_by(UaesRepairPlan.created_at.desc())
            .limit(1)
        )
        entity = result.scalars().first()
        return None if entity is None else self._to_domain(entity)

    async def list_plans(self, limit: int = 100) -> list[RepairPlan]:
        result = await self.session.execute(
            select(UaesRepairPlan).order_by(UaesRepairPlan.created_at.desc()).limit(limit)
        )
        return [self._to_domain(e) for e in result.scalars().all()]

    async def list_by_status(self, status: RepairStatus, limit: int = 100) -> list[RepairPlan]:
        result = await self.session.execute(
            select(UaesRepairPlan)
            .where(UaesRepairPlan.status == status.value)
            .order_by(UaesRepairPlan.created_at.desc())
            .limit(limit)
        )
        return [self._to_domain(e) for e in result.scalars().all()]

    async def list_history(self, limit: int = 100) -> list[RepairPlan]:
        return await self.list_plans(limit)

    async def update_status(self, plan_id: str, status: RepairStatus) -> None:
        entity = await self.session.get(UaesRepairPlan, plan_id)
        if entity:
            entity.status = status.value
            await self.session.flush()

    async def save_artifact(self, artifact: RepairArtifact) -> None:
        entity = UaesRepairArtifact(
            id=artifact.artifact_id,
            plan_id=artifact.plan_id,
            incident_id=artifact.incident_id,
            executed_at=artifact.executed_at,
            completed_at=artifact.completed_at,
            success=artifact.success,
            steps_completed=artifact.steps_completed,
            steps_total=artifact.steps_total,
            output=artifact.output,
            errors_json=list(artifact.errors),
            rollback_performed=artifact.rollback_performed,
            duration_seconds=artifact.duration_seconds,
        )
        self.session.add(entity)
        await self.session.flush()

    async def get_artifact(self, plan_id: str) -> RepairArtifact | None:
        result = await self.session.execute(
            select(UaesRepairArtifact)
            .where(UaesRepairArtifact.plan_id == plan_id)
            .order_by(UaesRepairArtifact.executed_at.desc())
            .limit(1)
        )
        entity = result.scalars().first()
        if entity is None:
            return None
        return RepairArtifact(
            artifact_id=entity.id,
            plan_id=entity.plan_id,
            incident_id=entity.incident_id,
            executed_at=entity.executed_at,
            completed_at=entity.completed_at,
            success=entity.success,
            steps_completed=entity.steps_completed,
            steps_total=entity.steps_total,
            output=entity.output,
            errors=list(entity.errors_json),
            rollback_performed=entity.rollback_performed,
            duration_seconds=entity.duration_seconds,
        )

    async def list_artifacts(self, limit: int = 100) -> list[RepairArtifact]:
        result = await self.session.execute(
            select(UaesRepairArtifact).order_by(UaesRepairArtifact.executed_at.desc()).limit(limit)
        )
        artifacts: list[RepairArtifact] = []
        for entity in result.scalars().all():
            artifacts.append(
                RepairArtifact(
                    artifact_id=entity.id,
                    plan_id=entity.plan_id,
                    incident_id=entity.incident_id,
                    executed_at=entity.executed_at,
                    completed_at=entity.completed_at,
                    success=entity.success,
                    steps_completed=entity.steps_completed,
                    steps_total=entity.steps_total,
                    output=entity.output,
                    errors=list(entity.errors_json),
                    rollback_performed=entity.rollback_performed,
                    duration_seconds=entity.duration_seconds,
                )
            )
        return artifacts

    def _to_domain(self, entity: UaesRepairPlan) -> RepairPlan:
        candidates = []
        for c in entity.candidates:
            risk = None
            if c.risk_json:
                risk = RepairRisk.model_validate(c.risk_json)
            confidence = None
            if c.confidence_json:
                confidence = ConfidenceDimensions.model_validate(c.confidence_json)
            cost = None
            if c.cost_json:
                cost = RepairCost.model_validate(c.cost_json)
            simulation = None
            if c.simulation_json:
                simulation = CandidateSimulation.model_validate(c.simulation_json)
            graph = None
            if c.repair_graph_json:
                graph = RepairGraph.model_validate(c.repair_graph_json)

            candidates.append(
                RepairCandidate(
                    candidate_id=c.id,
                    plan_id=c.plan_id,
                    repair_type=c.repair_type,
                    strategy_id=c.strategy_id,
                    strategy_name=c.strategy_name,
                    description=c.description,
                    score=c.score,
                    rank=c.rank,
                    estimated_duration_seconds=c.estimated_duration_seconds,
                    risk=risk,
                    confidence=confidence,
                    cost=cost,
                    constraints=[RepairConstraint.model_validate(ct) for ct in c.constraints_json],
                    steps=[],
                    repair_graph=graph,
                    simulation=simulation,
                    prerequisites=list(c.prerequisites_json),
                    affected_components=list(c.affected_components_json),
                )
            )

        selected = None
        if entity.selected_candidate_id:
            selected = next(
                (c for c in candidates if c.candidate_id == entity.selected_candidate_id),
                None,
            )

        approval = None
        if entity.approval_json:
            approval = ApprovalRequirement.model_validate(entity.approval_json)

        execution_plan = None
        if entity.execution_json:
            execution_plan = ExecutionPlan.model_validate(entity.execution_json)

        rollback_plan = None
        validation = None

        if execution_plan and execution_plan.rollback:
            rollback_plan = execution_plan.rollback
        if execution_plan and execution_plan.validation:
            validation = execution_plan.validation

        from app.operations.planner.domain.models import SimulationResult

        simulation_result = None
        if entity.simulation_json:
            simulation_result = SimulationResult.model_validate(entity.simulation_json)

        constraints = [RepairConstraint.model_validate(c) for c in entity.constraints_json]

        return RepairPlan(
            plan_id=entity.id,
            incident_id=entity.incident_id,
            status=entity.status,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            expires_at=entity.expires_at,
            selected_candidate=selected,
            candidates=candidates,
            constraints=constraints,
            approval=approval,
            execution_plan=execution_plan,
            rollback_plan=rollback_plan,
            validation=validation,
            simulation_result=simulation_result,
            planning_duration_ms=entity.planning_duration_ms,
            total_candidates_evaluated=entity.total_candidates_evaluated,
            strategy_used=entity.strategy_used,
            environment=entity.environment,
            component_type=entity.component_type,
            component_name=entity.component_name,
            knowledge_consulted=entity.knowledge_consulted,
            knowledge_snapshot_id=entity.knowledge_snapshot_id,
        )
