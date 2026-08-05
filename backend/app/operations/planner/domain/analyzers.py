"""Planner domain analyzers — deterministic, no AI/LLM."""

from __future__ import annotations

from app.operations.incidents.domain.enums import RootCauseCategory
from app.operations.planner.domain.enums import (
    ConstraintType,
    RepairGraphNodeType,
    RiskLevel,
    ValidationStage,
)
from app.operations.planner.domain.models import (
    ConfidenceDimensions,
    RepairCandidate,
    RepairConstraint,
    RepairCost,
    RepairGraph,
    RepairGraphNode,
    RepairPlan,
    RepairRisk,
    RepairType,
    RollbackPlan,
    RollbackReadinessCheck,
    ValidationCheck,
    ValidationPipelineResult,
)

# ---------------------------------------------------------------------------
# Risk Analyzer
# ---------------------------------------------------------------------------


class RiskAnalyzer:
    """5-factor deterministic risk scoring (0-100)."""

    def analyze(
        self,
        candidate: RepairCandidate,
        component_type: str,
        environment: str,
        root_cause_category: RootCauseCategory,
        root_cause_confidence: float,
    ) -> RepairRisk:
        score = 0.0
        factors: list[str] = []

        # Factor 1: Environment (0-30)
        if environment == "production":
            score += 30.0
            factors.append("Production environment increases risk")
        elif environment == "staging":
            score += 15.0
            factors.append("Staging environment")
        else:
            score += 5.0
            factors.append("Development environment — low risk")

        # Factor 2: Service criticality (0-25)
        critical_categories = {RootCauseCategory.DATABASE, RootCauseCategory.REDIS}
        if root_cause_category in critical_categories:
            score += 25.0
            factors.append(f"Critical service ({root_cause_category.value})")
        elif root_cause_category == RootCauseCategory.CODE:
            score += 15.0
            factors.append("Code-level issue")
        else:
            score += 5.0

        # Factor 3: Blast radius (0-20)
        blast_count = len(candidate.affected_components)
        blast_score = min(20.0, blast_count * 5.0)
        score += blast_score
        if blast_count > 0:
            factors.append(f"Affects {blast_count} component(s)")

        # Factor 4: Duration (0-15)
        if candidate.estimated_duration_seconds > 300:
            score += 15.0
            factors.append("Long repair duration (>5 minutes)")
        elif candidate.estimated_duration_seconds > 60:
            score += 8.0
            factors.append("Moderate repair duration")
        else:
            score += 2.0

        # Factor 5: Root cause confidence inverse (0-10)
        if root_cause_confidence < 0.5:
            score += 10.0
            factors.append("Low root cause confidence increases risk")
        elif root_cause_confidence < 0.8:
            score += 5.0
            factors.append("Moderate root cause confidence")

        score = max(0.0, min(100.0, score))
        level = _score_to_level(score)
        requires_backup = score > 50
        requires_maintenance = score > 80
        downtime = candidate.estimated_duration_seconds if score > 50 else 0

        return RepairRisk(
            score=score,
            level=level,
            factors=factors,
            mitigations=_suggest_mitigations(level, factors),
            blast_radius=list(candidate.affected_components),
            requires_backup=requires_backup,
            requires_maintenance_window=requires_maintenance,
            downtime_estimate_seconds=downtime,
        )


def _score_to_level(score: float) -> RiskLevel:
    if score <= 20:
        return RiskLevel.LOW
    if score <= 50:
        return RiskLevel.MEDIUM
    if score <= 80:
        return RiskLevel.HIGH
    if score <= 95:
        return RiskLevel.CRITICAL
    return RiskLevel.CATASTROPHIC


def _suggest_mitigations(level: RiskLevel, factors: list[str]) -> list[str]:
    mitigations: list[str] = []
    if level in (RiskLevel.HIGH, RiskLevel.CRITICAL, RiskLevel.CATASTROPHIC):
        mitigations.append("Ensure backup exists before execution")
    if level in (RiskLevel.CRITICAL, RiskLevel.CATASTROPHIC):
        mitigations.append("Schedule during maintenance window")
    if any("production" in f.lower() for f in factors):
        mitigations.append("Consider staging deployment first")
    if any("critical service" in f.lower() for f in factors):
        mitigations.append("Verify dependent services are healthy")
    return mitigations


# ---------------------------------------------------------------------------
# Confidence Analyzer
# ---------------------------------------------------------------------------


class ConfidenceAnalyzer:
    """4-dimension confidence scoring (evidence, root cause, repair, validation)."""

    def analyze(
        self,
        candidate: RepairCandidate,
        root_cause_confidence: float,
        evidence_categories: set[str],
        has_health_check: bool,
        has_metrics: bool,
        has_logs: bool,
        environment: str,
    ) -> ConfidenceDimensions:
        evidence_confidence = _evidence_confidence(evidence_categories)
        root_cause_conf = root_cause_confidence
        repair_conf = _repair_confidence(candidate)
        validation_conf = _validation_confidence(has_health_check, has_metrics, has_logs, candidate)

        dims = ConfidenceDimensions(
            evidence_confidence=evidence_confidence,
            root_cause_confidence=root_cause_conf,
            repair_confidence=repair_conf,
            validation_confidence=validation_conf,
            evidence_factors=_evidence_factors(evidence_categories),
            root_cause_factors=_root_cause_factors(root_cause_confidence),
            repair_factors=_repair_factors(candidate),
            validation_factors=_validation_factors(has_health_check, has_metrics, has_logs),
        )
        dims.compute_overall()
        return dims


def _evidence_confidence(categories: set[str]) -> float:
    expected = {"log", "metric", "config", "system"}
    if not expected:
        return 0.0
    return len(expected & categories) / len(expected)


def _repair_confidence(candidate: RepairCandidate) -> float:
    has_graph = candidate.repair_graph is not None and len(candidate.repair_graph.nodes) > 0
    has_steps = len(candidate.steps) > 0
    has_commands = False
    if has_graph:
        has_commands = any(
            n.command is not None
            for n in candidate.repair_graph.nodes  # type: ignore[union-attr]
        )
    elif has_steps:
        has_commands = any(s.command is not None for s in candidate.steps)
    completeness = 0.0
    if has_graph or has_steps:
        completeness = 0.6 if has_commands else 0.3
    has_affected = len(candidate.affected_components) > 0
    has_prereqs = len(candidate.prerequisites) > 0
    bonus = (0.2 if has_affected else 0.0) + (0.2 if has_prereqs else 0.0)
    return min(1.0, completeness + bonus)


def _validation_confidence(
    has_health: bool,
    has_metrics: bool,
    has_logs: bool,
    candidate: RepairCandidate,
) -> float:
    checks = sum([has_health, has_metrics, has_logs])
    base = checks / 3.0
    has_validation = False
    if candidate.repair_graph:
        has_validation = any(
            n.validation_command is not None
            for n in candidate.repair_graph.nodes  # type: ignore[union-attr]
        )
    elif candidate.steps:
        has_validation = any(s.validation_command is not None for s in candidate.steps)
    if has_validation:
        base = min(1.0, base + 0.3)
    return base


def _evidence_factors(categories: set[str]) -> list[str]:
    expected = {"log", "metric", "config", "system"}
    missing = expected - categories
    if not missing:
        return ["All expected evidence categories present"]
    return [f"Missing evidence category: {m}" for m in sorted(missing)]


def _root_cause_factors(rc_confidence: float) -> list[str]:
    if rc_confidence >= 0.8:
        return ["High root cause confidence"]
    if rc_confidence >= 0.5:
        return ["Moderate root cause confidence"]
    return ["Low root cause confidence — pattern may be ambiguous"]


def _repair_factors(candidate: RepairCandidate) -> list[str]:
    factors: list[str] = []
    if candidate.repair_graph and len(candidate.repair_graph.nodes) > 0:
        factors.append(f"Repair graph has {len(candidate.repair_graph.nodes)} nodes")
    elif candidate.steps:
        factors.append(f"Repair has {len(candidate.steps)} steps")
    else:
        factors.append("No repair steps defined")
    if candidate.affected_components:
        factors.append(f"Affects {len(candidate.affected_components)} component(s)")
    return factors


def _validation_factors(has_health: bool, has_metrics: bool, has_logs: bool) -> list[str]:
    factors: list[str] = []
    if has_health:
        factors.append("Health check available")
    if has_metrics:
        factors.append("Metrics available")
    if has_logs:
        factors.append("Logs available")
    if not factors:
        factors.append("No validation data available")
    return factors


# ---------------------------------------------------------------------------
# Cost Estimator
# ---------------------------------------------------------------------------


class CostEstimator:
    """Deterministic cost estimation for repair strategies."""

    def estimate(
        self,
        repair_type: RepairType,
        estimated_duration_seconds: int,
        affected_components: list[str],
    ) -> RepairCost:
        cpu = _cpu_impact(repair_type)
        mem = _memory_impact(repair_type)
        storage = _storage_impact(affected_components)
        network = _network_impact(repair_type)
        op_cost = _operational_cost(estimated_duration_seconds, cpu, mem, network)
        human = _human_effort(repair_type)
        downtime = estimated_duration_seconds if _requires_downtime(repair_type) else 0

        return RepairCost(
            execution_time_seconds=estimated_duration_seconds,
            cpu_impact_percent=cpu,
            memory_impact_mb=mem,
            storage_impact_mb=storage,
            network_impact=network,
            operational_cost=op_cost,
            human_effort_hours=human,
            requires_downtime=downtime > 0,
            downtime_seconds=downtime,
            description=f"Estimated cost for {repair_type.value}",
        )


def _cpu_impact(repair_type: RepairType) -> float:
    return {
        RepairType.SERVICE_RESTART: 10.0,
        RepairType.DATABASE_MAINTENANCE: 25.0,
        RepairType.REDIS_MAINTENANCE: 15.0,
        RepairType.RESOURCE_SCALING: 5.0,
        RepairType.DISK_CLEANUP: 20.0,
        RepairType.DEPLOYMENT_ROLLBACK: 15.0,
        RepairType.CACHE_CLEAR: 10.0,
        RepairType.PROCESS_KILL: 5.0,
        RepairType.DOCKER_RESTART: 10.0,
        RepairType.CONFIGURATION_CHANGE: 5.0,
        RepairType.DEPENDENCY_INSTALL: 8.0,
        RepairType.CODE_REVERT: 5.0,
        RepairType.ENVIRONMENT_VARIABLE_FIX: 3.0,
        RepairType.PERMISSION_FIX: 3.0,
        RepairType.LOG_ROTATION: 15.0,
        RepairType.MIGRATION_REPAIR: 20.0,
        RepairType.NETWORK_CHECK: 5.0,
        RepairType.MANUAL_INTERVENTION: 0.0,
    }.get(repair_type, 5.0)


def _memory_impact(repair_type: RepairType) -> float:
    return {
        RepairType.SERVICE_RESTART: 50.0,
        RepairType.DATABASE_MAINTENANCE: 200.0,
        RepairType.REDIS_MAINTENANCE: 100.0,
        RepairType.DISK_CLEANUP: 30.0,
        RepairType.DEPLOYMENT_ROLLBACK: 50.0,
        RepairType.LOG_ROTATION: 20.0,
    }.get(repair_type, 10.0)


def _storage_impact(affected_components: list[str]) -> float:
    if "disk" in affected_components:
        return 500.0
    if "database" in affected_components:
        return 100.0
    return 10.0


def _network_impact(repair_type: RepairType) -> str:
    if repair_type == RepairType.NETWORK_CHECK:
        return "medium"
    if repair_type in (
        RepairType.SERVICE_RESTART,
        RepairType.DOCKER_RESTART,
        RepairType.DEPLOYMENT_ROLLBACK,
    ):
        return "low"
    return "none"


def _operational_cost(exec_time: int, cpu: float, mem: float, network: str) -> float:
    time_score = min(30, exec_time / 10)
    cpu_score = cpu * 0.3
    mem_score = min(20, mem / 50)
    net_score = {"none": 0, "low": 5, "medium": 15, "high": 25}.get(network, 0)
    return round(min(100.0, time_score + cpu_score + mem_score + net_score), 2)


def _human_effort(repair_type: RepairType) -> float:
    if repair_type == RepairType.MANUAL_INTERVENTION:
        return 2.0
    if repair_type == RepairType.CONFIGURATION_CHANGE:
        return 0.5
    if repair_type == RepairType.CODE_REVERT:
        return 0.5
    return 0.0


def _requires_downtime(repair_type: RepairType) -> bool:
    return repair_type in {
        RepairType.SERVICE_RESTART,
        RepairType.DATABASE_MAINTENANCE,
        RepairType.REDIS_MAINTENANCE,
        RepairType.DOCKER_RESTART,
        RepairType.DEPLOYMENT_ROLLBACK,
        RepairType.CODE_REVERT,
    }


# ---------------------------------------------------------------------------
# Constraint Engine
# ---------------------------------------------------------------------------


class ConstraintEngine:
    """Evaluates and validates repair constraints."""

    def evaluate(
        self,
        component_type: str,
        environment: str,
        severity: str,
    ) -> list[RepairConstraint]:
        constraints: list[RepairConstraint] = []

        if environment == "production":
            constraints.append(
                RepairConstraint(
                    constraint_type=ConstraintType.REQUIRES_HUMAN_APPROVAL,
                    description="Production environment requires human approval",
                    parameters={"role": "maintainer"},
                    severity="hard",
                    created_by="policy",
                )
            )
            constraints.append(
                RepairConstraint(
                    constraint_type=ConstraintType.REQUIRES_BACKUP,
                    description="Production repairs require backup verification",
                    parameters={"backup_type": "full"},
                    severity="hard",
                    created_by="policy",
                )
            )

        if severity in ("critical", "emergency"):
            constraints.append(
                RepairConstraint(
                    constraint_type=ConstraintType.MAX_DOWNTIME,
                    description="Critical incidents require minimal downtime",
                    parameters={"max_seconds": "300"},
                    severity="hard",
                    created_by="policy",
                )
            )

        if component_type in ("database", "redis"):
            constraints.append(
                RepairConstraint(
                    constraint_type=ConstraintType.NO_DATA_LOSS,
                    description="Data service repairs must not cause data loss",
                    severity="hard",
                    created_by="system",
                )
            )

        return constraints

    def satisfies(
        self,
        candidate: RepairCandidate,
        constraints: list[RepairConstraint],
    ) -> tuple[bool, list[str]]:
        violations: list[str] = []
        for constraint in constraints:
            if constraint.severity != "hard":
                continue
            if not _check_constraint(candidate, constraint):
                violations.append(
                    f"Violates {constraint.constraint_type}: {constraint.description}"
                )
        return len(violations) == 0, violations


def _check_constraint(candidate: RepairCandidate, constraint: RepairConstraint) -> bool:
    repair_type_val = (
        candidate.repair_type
        if isinstance(candidate.repair_type, str)
        else candidate.repair_type.value
    )
    if constraint.constraint_type == ConstraintType.NO_DATA_LOSS:
        return repair_type_val not in ("code_revert",)
    if constraint.constraint_type == ConstraintType.REQUIRES_BACKUP:
        return True
    if constraint.constraint_type == ConstraintType.MAX_DOWNTIME:
        max_seconds = int(constraint.parameters.get("max_seconds", "3600"))
        return candidate.estimated_duration_seconds <= max_seconds
    if constraint.constraint_type == ConstraintType.ENVIRONMENT_RESTRICTED:
        allowed = constraint.parameters.get("allowed", "").split(",")
        return repair_type_val in allowed if allowed else True
    return True


# ---------------------------------------------------------------------------
# Rollback Planner
# ---------------------------------------------------------------------------


class RollbackPlanner:
    """Generates rollback plans from candidate repair steps."""

    def generate(
        self,
        candidate: RepairCandidate,
        plan_id: str,
    ) -> RollbackPlan:
        rollback_nodes: list[RepairGraphNode] = []
        edges: list[tuple[str, str]] = []
        total_duration = 0

        if candidate.repair_graph:
            for node in reversed(candidate.repair_graph.nodes):
                if node.rollback_command:
                    rb_node = RepairGraphNode(
                        node_type=RepairGraphNodeType.ROLLBACK,
                        action=f"rollback_{node.action}",
                        command=node.rollback_command,
                        dependencies=[],
                        timeout_seconds=node.timeout_seconds * 2,
                        can_fail=False,
                        estimated_duration_seconds=node.estimated_duration_seconds * 2,
                    )
                    rollback_nodes.append(rb_node)
                    total_duration += rb_node.estimated_duration_seconds
        elif candidate.steps:
            for step in reversed(candidate.steps):
                if step.rollback_command:
                    rb_node = RepairGraphNode(
                        node_type=RepairGraphNodeType.ROLLBACK,
                        action=f"rollback_{step.action}",
                        command=step.rollback_command,
                        dependencies=[],
                        timeout_seconds=step.timeout_seconds * 2,
                        can_fail=False,
                        estimated_duration_seconds=step.estimated_duration_seconds * 2,
                    )
                    rollback_nodes.append(rb_node)
                    total_duration += rb_node.estimated_duration_seconds

        if not rollback_nodes:
            rollback_nodes.append(
                RepairGraphNode(
                    node_type=RepairGraphNodeType.ROLLBACK,
                    action="manual_rollback_required",
                    command=None,
                    estimated_duration_seconds=0,
                    can_fail=False,
                )
            )
            return RollbackPlan(
                plan_id=plan_id,
                steps=rollback_nodes,
                estimated_duration_seconds=0,
                automatic=False,
                requires_manual_intervention=True,
                description="No automatic rollback available — manual intervention required",
            )

        for i in range(1, len(rollback_nodes)):
            edges.append((rollback_nodes[i - 1].node_id, rollback_nodes[i].node_id))

        graph = RepairGraph(
            nodes=rollback_nodes,
            edges=edges,
            entry_nodes=[rollback_nodes[0].node_id] if rollback_nodes else [],
            exit_nodes=[rollback_nodes[-1].node_id] if rollback_nodes else [],
        )

        return RollbackPlan(
            plan_id=plan_id,
            graph=graph,
            steps=rollback_nodes,
            estimated_duration_seconds=total_duration,
            automatic=True,
            requires_manual_intervention=False,
            description=f"Automatic rollback for {candidate.strategy_name}",
        )


# ---------------------------------------------------------------------------
# Validation Planner
# ---------------------------------------------------------------------------


class ValidationPlanner:
    """Generates validation checks and rollback readiness assessments."""

    def generate_pre_approval_checks(
        self,
        plan: RepairPlan,
    ) -> ValidationPipelineResult:
        checks: list[ValidationCheck] = []

        if plan.selected_candidate:
            checks.append(
                ValidationCheck(
                    name="rollback_available",
                    check_type="constraint",
                    stage=ValidationStage.PRE_APPROVAL,
                )
            )
            checks.append(
                ValidationCheck(
                    name="constraints_satisfied",
                    check_type="constraint",
                    stage=ValidationStage.CONSTRAINT_VERIFICATION,
                )
            )

        if plan.environment == "production":
            checks.append(
                ValidationCheck(
                    name="production_safety",
                    check_type="constraint",
                    stage=ValidationStage.PRE_APPROVAL,
                )
            )

        passed: list[str] = []
        failed: list[str] = []

        for check in checks:
            if plan.selected_candidate and plan.selected_candidate.risk:
                if plan.selected_candidate.risk.level in ("low", "medium"):
                    passed.append(check.check_id)
                else:
                    failed.append(check.check_id)
            else:
                passed.append(check.check_id)

        return ValidationPipelineResult(
            plan_id=plan.plan_id,
            checks=checks,
            passed=passed,
            failed=failed,
            all_passed=len(failed) == 0,
        )

    def check_rollback_readiness(
        self,
        plan: RepairPlan,
    ) -> RollbackReadinessCheck:
        has_rollback = plan.rollback_plan is not None
        steps_validated = 0
        steps_total = 0
        issues: list[str] = []

        if plan.rollback_plan:
            steps_total = len(plan.rollback_plan.steps)
            steps_validated = steps_total
            if not plan.rollback_plan.automatic:
                issues.append("Rollback is not automatic")
            if plan.rollback_plan.estimated_duration_seconds == 0 and steps_total > 0:
                issues.append("Rollback duration not estimated")

        if not has_rollback:
            issues.append("No rollback plan available")

        return RollbackReadinessCheck(
            plan_id=plan.plan_id,
            rollback_available=has_rollback,
            rollback_automatic=has_rollback
            and (plan.rollback_plan.automatic if plan.rollback_plan else False),
            rollback_steps_validated=steps_validated,
            rollback_steps_total=steps_total,
            estimated_rollback_duration_seconds=(
                plan.rollback_plan.estimated_duration_seconds if plan.rollback_plan else 0
            ),
            issues=issues,
        )


# ---------------------------------------------------------------------------
# Repair Graph Builder
# ---------------------------------------------------------------------------


def build_graph_from_strategy(
    steps_template: list[dict[str, str]],
    target: str,
    estimated_duration: int,
) -> RepairGraph:
    """Build a deterministic RepairGraph from a strategy's step template."""
    nodes: list[RepairGraphNode] = []
    edges: list[tuple[str, str]] = []
    step_duration = estimated_duration // max(len(steps_template), 1)

    for i, step in enumerate(steps_template):
        action = step.get("action", f"step_{i}")
        node_type = RepairGraphNodeType.ACTION
        if "check" in action or "verify" in action or "ping" in action:
            node_type = RepairGraphNodeType.CHECK
        elif "decision" in action:
            node_type = RepairGraphNodeType.DECISION

        node = RepairGraphNode(
            node_type=node_type,
            action=f"{action}_{target}",
            command=f"{action} {target}",
            dependencies=[],
            timeout_seconds=300,
            can_fail=False,
            rollback_command=f"rollback_{action}_{target}",
            validation_command=f"verify_{action}_{target}",
            estimated_duration_seconds=step_duration,
        )
        nodes.append(node)

        if i > 0:
            edges.append((nodes[i - 1].node_id, node.node_id))

    if len(nodes) > 1:
        return RepairGraph(
            nodes=nodes,
            edges=list(edges),
            entry_nodes=[nodes[0].node_id],
            exit_nodes=[nodes[-1].node_id],
        )

    return RepairGraph(
        nodes=nodes,
        edges=[],
        entry_nodes=[n.node_id for n in nodes],
        exit_nodes=[n.node_id for n in nodes],
    )
