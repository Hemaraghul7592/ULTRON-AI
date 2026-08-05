from __future__ import annotations

from dataclasses import dataclass

from app.operations.domain.value_objects import ConfidenceScore
from app.operations.incidents.domain.enums import (
    RecommendedAction,
    RootCauseCategory,
)
from app.operations.incidents.domain.models import (
    EvidenceBundle,
    Incident,
    RecoveryRecommendation,
    RootCause,
)


@dataclass
class Rule:
    name: str
    condition: str
    category: RootCauseCategory
    confidence: float
    action: RecommendedAction
    description: str


class RootCauseAnalyzer:
    def __init__(self) -> None:
        self.rules = self._build_rules()

    def _build_rules(self) -> list[Rule]:
        return [
            Rule(
                name="database_connection_refused",
                condition="database_connection_refused",
                category=RootCauseCategory.DATABASE,
                confidence=0.95,
                action=RecommendedAction.RESTART_DATABASE,
                description="Database connection refused - database service likely offline",
            ),
            Rule(
                name="database_timeout",
                condition="database_timeout",
                category=RootCauseCategory.DATABASE,
                confidence=0.85,
                action=RecommendedAction.RESTART_DATABASE,
                description="Database queries timing out - possible overload or lock contention",
            ),
            Rule(
                name="database_auth_failure",
                condition="database_auth_failure",
                category=RootCauseCategory.DATABASE,
                confidence=0.9,
                action=RecommendedAction.FIX_CONFIGURATION,
                description="Database authentication failed - check credentials",
            ),
            Rule(
                name="redis_connection_refused",
                condition="redis_connection_refused",
                category=RootCauseCategory.REDIS,
                confidence=0.95,
                action=RecommendedAction.RESTART_REDIS,
                description="Redis connection refused - Redis service likely offline",
            ),
            Rule(
                name="redis_timeout",
                condition="redis_timeout",
                category=RootCauseCategory.REDIS,
                confidence=0.85,
                action=RecommendedAction.RESTART_REDIS,
                description="Redis commands timing out - possible memory pressure",
            ),
            Rule(
                name="network_dns_failure",
                condition="network_dns_failure",
                category=RootCauseCategory.NETWORK,
                confidence=0.9,
                action=RecommendedAction.CHECK_NETWORK,
                description="DNS resolution failed - network connectivity issue",
            ),
            Rule(
                name="network_timeout",
                condition="network_timeout",
                category=RootCauseCategory.NETWORK,
                confidence=0.8,
                action=RecommendedAction.CHECK_NETWORK,
                description="Network requests timing out - connectivity or firewall issue",
            ),
            Rule(
                name="memory_oom",
                condition="memory_oom",
                category=RootCauseCategory.MEMORY,
                confidence=0.95,
                action=RecommendedAction.SCALE_RESOURCES,
                description="Out of memory - process killed by OOM killer",
            ),
            Rule(
                name="memory_high_pressure",
                condition="memory_high_pressure",
                category=RootCauseCategory.MEMORY,
                confidence=0.8,
                action=RecommendedAction.SCALE_RESOURCES,
                description="Memory usage above threshold - potential leak or load spike",
            ),
            Rule(
                name="cpu_saturation",
                condition="cpu_saturation",
                category=RootCauseCategory.CPU,
                confidence=0.8,
                action=RecommendedAction.SCALE_RESOURCES,
                description="CPU usage saturated - insufficient compute resources",
            ),
            Rule(
                name="disk_full",
                condition="disk_full",
                category=RootCauseCategory.DISK,
                confidence=0.95,
                action=RecommendedAction.FREE_DISK_SPACE,
                description="Disk space exhausted - cannot write logs or data",
            ),
            Rule(
                name="disk_high_usage",
                condition="disk_high_usage",
                category=RootCauseCategory.DISK,
                confidence=0.8,
                action=RecommendedAction.FREE_DISK_SPACE,
                description="Disk usage above threshold - cleanup needed",
            ),
            Rule(
                name="import_error",
                condition="import_error",
                category=RootCauseCategory.DEPENDENCY,
                confidence=0.9,
                action=RecommendedAction.INSTALL_DEPENDENCY,
                description="Python ImportError - missing or broken dependency",
            ),
            Rule(
                name="module_not_found",
                condition="module_not_found",
                category=RootCauseCategory.DEPENDENCY,
                confidence=0.9,
                action=RecommendedAction.INSTALL_DEPENDENCY,
                description="ModuleNotFoundError - dependency not installed",
            ),
            Rule(
                name="circular_dependency",
                condition="circular_dependency",
                category=RootCauseCategory.DEPENDENCY,
                confidence=0.85,
                action=RecommendedAction.REVERT_CODE,
                description="Circular import detected - code structure issue",
            ),
            Rule(
                name="di_registration_error",
                condition="di_registration_error",
                category=RootCauseCategory.DEPENDENCY,
                confidence=0.85,
                action=RecommendedAction.REVERT_CODE,
                description="Dependency injection registration failed - startup issue",
            ),
            Rule(
                name="config_missing_key",
                condition="config_missing_key",
                category=RootCauseCategory.CONFIGURATION,
                confidence=0.9,
                action=RecommendedAction.FIX_CONFIGURATION,
                description="Required configuration key missing or invalid",
            ),
            Rule(
                name="config_invalid_value",
                condition="config_invalid_value",
                category=RootCauseCategory.CONFIGURATION,
                confidence=0.85,
                action=RecommendedAction.FIX_CONFIGURATION,
                description="Configuration value invalid - type or format mismatch",
            ),
            Rule(
                name="deployment_failed",
                condition="deployment_failed",
                category=RootCauseCategory.DEPLOYMENT,
                confidence=0.9,
                action=RecommendedAction.ROLLBACK_DEPLOYMENT,
                description="Deployment failed - rollback to previous version recommended",
            ),
            Rule(
                name="syntax_error",
                condition="syntax_error",
                category=RootCauseCategory.CODE,
                confidence=0.95,
                action=RecommendedAction.REVERT_CODE,
                description="SyntaxError in code - broken deployment",
            ),
            Rule(
                name="runtime_error",
                condition="runtime_error",
                category=RootCauseCategory.CODE,
                confidence=0.7,
                action=RecommendedAction.INVESTIGATE_MANUALLY,
                description="Unhandled runtime exception - manual investigation needed",
            ),
            Rule(
                name="github_actions_failure",
                condition="github_actions_failure",
                category=RootCauseCategory.DEPLOYMENT,
                confidence=0.85,
                action=RecommendedAction.ROLLBACK_DEPLOYMENT,
                description="GitHub Actions workflow failed - CI/CD pipeline issue",
            ),
            Rule(
                name="docker_unhealthy",
                condition="docker_unhealthy",
                category=RootCauseCategory.DEPLOYMENT,
                confidence=0.8,
                action=RecommendedAction.RESTART_SERVICE,
                description="Docker container unhealthy - restart or check logs",
            ),
        ]

    def _match_condition(self, condition: str, evidence_bundle: EvidenceBundle, incident: Incident) -> bool:
        evidence_text = " ".join([e.redacted_excerpt.lower() for e in evidence_bundle.evidence])
        incident_text = (incident.detailed_description + " " + incident.summary).lower()

        combined_text = evidence_text + " " + incident_text

        condition_patterns = {
            "database_connection_refused": [
                "connection refused",
                "could not connect to database",
                "connection to server",
                "psycopg2.OperationalError",
                "asyncpg.exceptions.CannotConnectNowError",
                "sqlalchemy.exc.OperationalError",
            ],
            "database_timeout": [
                "timeout",
                "query timeout",
                "statement timeout",
                "lock wait timeout",
            ],
            "database_auth_failure": [
                "authentication failed",
                "password authentication failed",
                "invalid password",
                "role does not exist",
            ],
            "redis_connection_refused": [
                "connection refused",
                "could not connect to redis",
                "redis.exceptions.ConnectionError",
                "aioredis.exceptions.ConnectionError",
            ],
            "redis_timeout": [
                "redis timeout",
                "command timed out",
                "redis.exceptions.TimeoutError",
            ],
            "network_dns_failure": [
                "dns",
                "name resolution",
                "getaddrinfo failed",
                "socket.gaierror",
            ],
            "network_timeout": [
                "connection timeout",
                "connect timeout",
                "read timeout",
                "request timeout",
            ],
            "memory_oom": [
                "out of memory",
                "oom killed",
                "memoryerror",
                "killed process",
            ],
            "memory_high_pressure": [
                "memory usage",
                "memory percent",
                "high memory",
                "low memory",
            ],
            "cpu_saturation": [
                "cpu percent",
                "cpu usage",
                "high cpu",
                "cpu saturation",
            ],
            "disk_full": [
                "no space left",
                "disk full",
                "enospc",
                "disk quota exceeded",
            ],
            "disk_high_usage": [
                "disk usage",
                "disk percent",
                "high disk",
                "low disk space",
            ],
            "import_error": [
                "importerror",
                "cannot import",
                "no module named",
            ],
            "module_not_found": [
                "modulenotfounderror",
                "no module named",
            ],
            "circular_dependency": [
                "circular import",
                "import cycle",
                "circular dependency",
            ],
            "di_registration_error": [
                "dependency injection",
                "di container",
                "registration failed",
                "service not registered",
            ],
            "config_missing_key": [
                "missing configuration",
                "config not found",
                "required key",
                "environment variable not set",
            ],
            "config_invalid_value": [
                "invalid configuration",
                "invalid config",
                "configuration error",
                "value error",
            ],
            "deployment_failed": [
                "deployment failed",
                "deploy failed",
                "rollback",
                "release failed",
            ],
            "syntax_error": [
                "syntaxerror",
                "invalid syntax",
                "syntax error",
            ],
            "runtime_error": [
                "runtimeerror",
                "exception",
                "traceback",
            ],
            "github_actions_failure": [
                "github actions",
                "workflow failed",
                "ci failed",
                "actions failed",
            ],
            "docker_unhealthy": [
                "docker unhealthy",
                "container unhealthy",
                "health check failed",
            ],
        }

        patterns = condition_patterns.get(condition, [condition])
        return any(pattern in combined_text for pattern in patterns)

    def analyze(self, incident: Incident, evidence_bundle: EvidenceBundle) -> RootCause:
        matched_rules = []

        for rule in self.rules:
            if self._match_condition(rule.condition, evidence_bundle, incident):
                matched_rules.append(rule)

        if not matched_rules:
            return RootCause(
                incident_id=incident.incident_id,
                category=RootCauseCategory.UNKNOWN,
                description="No matching root cause pattern found - manual investigation required",
                confidence=ConfidenceScore(value=0.1),
                supporting_evidence=[],
                rule_matched="none",
            )

        matched_rules.sort(key=lambda r: r.confidence, reverse=True)
        best_rule = matched_rules[0]

        supporting_evidence = []
        for evidence in evidence_bundle.evidence:
            if any(pattern in evidence.redacted_excerpt.lower() for pattern in [best_rule.condition.replace("_", " ")]):
                supporting_evidence.append(evidence.evidence_id)

        return RootCause(
            incident_id=incident.incident_id,
            category=best_rule.category,
            description=best_rule.description,
            confidence=ConfidenceScore(value=best_rule.confidence),
            supporting_evidence=supporting_evidence,
            rule_matched=best_rule.name,
        )

    def recommend_recovery(self, root_cause: RootCause) -> RecoveryRecommendation:
        rule = next((r for r in self.rules if r.name == root_cause.rule_matched), None)

        if rule is None:
            return RecoveryRecommendation(
                action=RecommendedAction.INVESTIGATE_MANUALLY,
                description="Unable to determine automated recovery action - manual investigation required",
                confidence=ConfidenceScore(value=0.3),
                estimated_impact="Unknown",
                prerequisites=[],
                steps=["Review incident details and evidence manually", "Check system logs and metrics", "Contact on-call engineer if needed"],
            )

        return RecoveryRecommendation(
            action=rule.action,
            description=f"Automated recommendation based on rule: {rule.name}",
            confidence=ConfidenceScore(value=rule.confidence * 0.9),
            estimated_impact="Medium" if rule.confidence > 0.8 else "Low",
            prerequisites=[],
            steps=[f"Execute: {rule.action.value.replace('_', ' ').title()}", "Verify system health after action", "Monitor for recurrence"],
        )
