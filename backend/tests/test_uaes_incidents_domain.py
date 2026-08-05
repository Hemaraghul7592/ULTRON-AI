from __future__ import annotations

import pytest

from app.operations.domain.value_objects import ConfidenceScore
from app.operations.incidents.domain.analyzer import RootCauseAnalyzer
from app.operations.incidents.domain.enums import (
    EvidenceCategory,
    IncidentSeverity,
    IncidentStatus,
    InvestigationStatus,
    RecommendedAction,
    RootCauseCategory,
)
from app.operations.incidents.domain.models import (
    EvidenceBundle,
    Incident,
    IncidentEvidence,
    RootCause,
)


def _incident(**overrides) -> Incident:
    base = {
        "severity": IncidentSeverity.HIGH,
        "component_type": "backend",
        "component_name": "api",
        "environment": "production",
        "summary": "api degraded",
        "detailed_description": "The API component is degraded",
    }
    base.update(overrides)
    return Incident(**base)


def _evidence(excerpt: str, category=EvidenceCategory.LOG, source: str = "log") -> IncidentEvidence:
    return IncidentEvidence(
        incident_id="incident-1",
        category=category,
        source=source,
        payload_ref="ref",
        redacted_excerpt=excerpt,
        checksum="c" * 32,
    )


def _bundle(*items: IncidentEvidence) -> EvidenceBundle:
    return EvidenceBundle(incident_id="incident-1", evidence=list(items))


def test_enums_have_expected_members() -> None:
    assert IncidentStatus.DETECTED.value == "detected"
    assert IncidentStatus.WAITING_FOR_REPAIR.value == "waiting_for_repair"
    assert IncidentSeverity.EMERGENCY.value == "emergency"
    assert InvestigationStatus.COMPLETED.value == "completed"
    assert EvidenceCategory.DEPLOYMENT.value == "deployment"
    assert RootCauseCategory.REDIS.value == "redis"
    assert RecommendedAction.RESTART_SERVICE.value == "restart_service"


def test_incident_defaults() -> None:
    incident = _incident()
    assert incident.status == IncidentStatus.DETECTED.value
    assert incident.incident_id
    assert incident.confidence.value == 0.0
    assert incident.tags == {}


def test_incident_requires_summary() -> None:
    with pytest.raises(ValueError, match="summary"):
        Incident(
            severity=IncidentSeverity.HIGH,
            component_type="backend",
            component_name="api",
            environment="production",
            summary="",
            detailed_description="desc",
        )


def test_incident_round_trip() -> None:
    incident = _incident(tags={"source": "test"})
    data = incident.to_dict()
    restored = Incident.from_dict(data)
    assert restored.incident_id == incident.incident_id
    assert restored.tags == {"source": "test"}


def test_evidence_bundle_defaults() -> None:
    bundle = _bundle()
    assert bundle.evidence == []
    assert bundle.failed_collectors == []
    assert bundle.collection_duration_ms == 0


def test_analyzer_matches_database_connection_refused() -> None:
    analyzer = RootCauseAnalyzer()
    incident = _incident()
    bundle = _bundle(_evidence("psycopg2.OperationalError: connection refused"))
    root_cause = analyzer.analyze(incident, bundle)
    assert root_cause.category == RootCauseCategory.DATABASE.value
    assert root_cause.confidence.value >= 0.9


def test_analyzer_matches_redis_from_incident_text() -> None:
    analyzer = RootCauseAnalyzer()
    incident = _incident(detailed_description="could not connect to redis server")
    bundle = _bundle()
    root_cause = analyzer.analyze(incident, bundle)
    assert root_cause.category == RootCauseCategory.REDIS.value


def test_analyzer_matches_memory_oom() -> None:
    analyzer = RootCauseAnalyzer()
    incident = _incident()
    bundle = _bundle(_evidence("process was oom killed by kernel"))
    root_cause = analyzer.analyze(incident, bundle)
    assert root_cause.category == RootCauseCategory.MEMORY.value


def test_analyzer_matches_disk_full() -> None:
    analyzer = RootCauseAnalyzer()
    incident = _incident()
    bundle = _bundle(_evidence("OSError: no space left on device"))
    root_cause = analyzer.analyze(incident, bundle)
    assert root_cause.category == RootCauseCategory.DISK.value


def test_analyzer_matches_import_error() -> None:
    analyzer = RootCauseAnalyzer()
    incident = _incident()
    bundle = _bundle(_evidence("ModuleNotFoundError: no module named 'foo'"))
    root_cause = analyzer.analyze(incident, bundle)
    assert root_cause.category == RootCauseCategory.DEPENDENCY.value


def test_analyzer_returns_unknown_when_no_match() -> None:
    analyzer = RootCauseAnalyzer()
    incident = _incident(detailed_description="everything looks fine")
    bundle = _bundle(_evidence("all systems nominal"))
    root_cause = analyzer.analyze(incident, bundle)
    assert root_cause.category == RootCauseCategory.UNKNOWN.value
    assert root_cause.rule_matched == "none"


def test_analyzer_picks_highest_confidence_rule() -> None:
    analyzer = RootCauseAnalyzer()
    incident = _incident()
    bundle = _bundle(
        _evidence("psycopg2.OperationalError: connection refused to database")
    )
    root_cause = analyzer.analyze(incident, bundle)
    assert root_cause.rule_matched == "database_connection_refused"


def test_analyzer_collects_supporting_evidence() -> None:
    analyzer = RootCauseAnalyzer()
    incident = _incident()
    matching = _evidence("database connection refused error occurred")
    bundle = _bundle(matching, _evidence("unrelated log line"))
    root_cause = analyzer.analyze(incident, bundle)
    assert matching.evidence_id in root_cause.supporting_evidence


def test_analyzer_has_23_rules() -> None:
    analyzer = RootCauseAnalyzer()
    assert len(analyzer.rules) == 23


def test_recommend_recovery_for_known_rule() -> None:
    analyzer = RootCauseAnalyzer()
    root_cause = RootCause(
        incident_id="incident-1",
        category=RootCauseCategory.DATABASE,
        description="db down",
        confidence=ConfidenceScore(value=0.95),
        rule_matched="database_connection_refused",
    )
    recommendation = analyzer.recommend_recovery(root_cause)
    assert recommendation.action == RecommendedAction.RESTART_DATABASE.value
    assert recommendation.steps


def test_recommend_recovery_for_unknown_rule() -> None:
    analyzer = RootCauseAnalyzer()
    root_cause = RootCause(
        incident_id="incident-1",
        category=RootCauseCategory.UNKNOWN,
        description="unknown",
        confidence=ConfidenceScore(value=0.1),
        rule_matched="none",
    )
    recommendation = analyzer.recommend_recovery(root_cause)
    assert recommendation.action == RecommendedAction.INVESTIGATE_MANUALLY.value
