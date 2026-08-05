from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

from app.operations.domain.value_objects import ConfidenceScore
from app.operations.incidents.application.diagnostic_pack import DiagnosticPackGenerator
from app.operations.incidents.application.evidence_service import EvidenceCollectionService
from app.operations.incidents.application.investigation_service import InvestigationService
from app.operations.incidents.application.ports import (
    DiagnosticPackPort,
    EvidenceCollectorPort,
    RootCauseAnalysisPort,
)
from app.operations.incidents.application.publisher import InMemoryInvestigationPublisher
from app.operations.incidents.domain.enums import (
    EvidenceCategory,
    IncidentSeverity,
    IncidentStatus,
    InvestigationStatus,
    RecommendedAction,
    RootCauseCategory,
)
from app.operations.incidents.domain.models import (
    DiagnosticPack,
    EvidenceBundle,
    Incident,
    IncidentEvidence,
    RecoveryRecommendation,
    RootCause,
)
from app.operations.incidents.infrastructure.collectors.base import BaseCollector


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


def _evidence(
    excerpt: str = "test evidence",
    category: EvidenceCategory = EvidenceCategory.LOG,
    source: str = "test_collector",
) -> IncidentEvidence:
    return IncidentEvidence(
        incident_id="incident-1",
        category=category,
        source=source,
        payload_ref="ref",
        redacted_excerpt=excerpt,
        checksum="c" * 32,
    )


def _root_cause(
    category: RootCauseCategory = RootCauseCategory.DATABASE,
    confidence: float = 0.95,
) -> RootCause:
    return RootCause(
        incident_id="incident-1",
        category=category,
        description="database connection refused",
        confidence=ConfidenceScore(value=confidence),
        supporting_evidence=[],
        rule_matched="database_connection_refused",
    )


def _recovery() -> RecoveryRecommendation:
    return RecoveryRecommendation(
        action=RecommendedAction.RESTART_DATABASE,
        description="restart the database",
        confidence=ConfidenceScore(value=0.85),
        estimated_impact="High",
    )


def _bundle(*items: IncidentEvidence) -> EvidenceBundle:
    return EvidenceBundle(incident_id="incident-1", evidence=list(items))


def test_evidence_collector_service_runs_all_collectors() -> None:
    col1 = BaseCollector()
    col1.name = "col1"
    col1.category = EvidenceCategory.LOG
    col2 = BaseCollector()
    col2.name = "col2"
    col2.category = EvidenceCategory.METRIC

    service = EvidenceCollectionService(collectors=[col1, col2])
    incident = _incident()

    async def _run():
        return await service.collect_evidence(incident)

    bundle = asyncio.get_event_loop().run_until_complete(_run())
    # Both collectors raise NotImplementedError → caught by _collect_one → fail
    # The evidence items will have error metadata from collect_error
    assert isinstance(bundle, EvidenceBundle)
    assert bundle.incident_id == incident.incident_id


def test_evidence_collector_service_collect_error_handling() -> None:
    class FailingCollector(BaseCollector):
        name = "failing"
        category = EvidenceCategory.LOG

        async def collect(self, incident):
            raise RuntimeError("boom")

    service = EvidenceCollectionService(collectors=[FailingCollector()])
    incident = _incident()

    async def _run():
        return await service.collect_evidence(incident)

    bundle = asyncio.get_event_loop().run_until_complete(_run())
    # The failure is caught and recorded via collect_error
    assert "failing" in bundle.failed_collectors


def test_evidence_collector_register() -> None:
    service = EvidenceCollectionService(collectors=[])
    assert len(service.collectors) == 0

    class DummyCollector(BaseCollector):
        name = "dummy"

    service.register(DummyCollector())
    assert len(service.collectors) == 1


def test_diagnostic_pack_generator_builds_pack() -> None:
    generator = DiagnosticPackGenerator()
    incident = _incident()
    bundle = _bundle(
        _evidence("test log line", EvidenceCategory.LOG, "fastapi_logs"),
        _evidence('{"cpu_percent": 95.0}', EvidenceCategory.METRIC, "cpu_status"),
        _evidence('{"database": "ok"}', EvidenceCategory.CONFIG, "config"),
    )
    root_cause = _root_cause()
    recovery = _recovery()

    async def _run():
        return generator.generate(incident, bundle, root_cause, recovery)

    pack = asyncio.get_event_loop().run_until_complete(_run())
    assert isinstance(pack, DiagnosticPack)
    assert pack.incident_id == incident.incident_id
    assert pack.summary
    assert len(pack.timeline) >= 2
    assert "test log line" in pack.logs[0]
    assert pack.metrics.get("cpu_status")
    assert pack.configuration.get("config")
    assert pack.root_cause is not None
    assert pack.recovery_recommendation is not None


def test_diagnostic_pack_generator_empty_bundle() -> None:
    generator = DiagnosticPackGenerator()
    incident = _incident()
    bundle = _bundle()
    root_cause = _root_cause()
    recovery = _recovery()

    pack = generator.generate(incident, bundle, root_cause, recovery)
    assert pack.logs == []
    assert pack.metrics == {}
    assert len(pack.timeline) >= 2


def test_in_memory_publisher_stores_events() -> None:
    publisher = InMemoryInvestigationPublisher()
    assert publisher.events == []

    event = MagicMock()
    event.event_type = "test_event"
    asyncio.get_event_loop().run_until_complete(publisher.publish(event))
    assert len(publisher.events) == 1
    assert publisher.events[0].event_type == "test_event"


def test_in_memory_publisher_clear() -> None:
    publisher = InMemoryInvestigationPublisher()
    event = MagicMock()
    event.event_type = "test"
    asyncio.get_event_loop().run_until_complete(publisher.publish(event))
    publisher.clear()
    assert publisher.events == []


def test_in_memory_publisher_bounded() -> None:
    publisher = InMemoryInvestigationPublisher(max_events=5)
    for i in range(10):
        event = MagicMock()
        event.event_type = f"event_{i}"
        asyncio.get_event_loop().run_until_complete(publisher.publish(event))
    assert len(publisher.events) == 5
    assert publisher.events[0].event_type == "event_5"


def test_investigation_service_complete_flow() -> None:
    incident = _incident()
    bundle = _bundle(_evidence("database connection refused"))
    root_cause = _root_cause()
    recovery = _recovery()
    pack = DiagnosticPack(
        incident_id=incident.incident_id,
        summary="test pack",
        root_cause=root_cause,
        confidence_score=ConfidenceScore(value=0.95),
        recovery_recommendation=recovery,
    )

    mock_repo = AsyncMock()
    mock_repo.save = AsyncMock()
    mock_repo.add_evidence = AsyncMock()
    mock_repo.add_root_cause = AsyncMock()
    mock_repo.add_diagnostic_pack = AsyncMock()

    mock_collector = AsyncMock(spec=EvidenceCollectorPort)
    mock_collector.collect_evidence = AsyncMock(return_value=bundle)

    mock_analyzer = MagicMock(spec=RootCauseAnalysisPort)
    mock_analyzer.analyze = MagicMock(return_value=root_cause)
    mock_analyzer.recommend_recovery = MagicMock(return_value=recovery)

    mock_pack_gen = MagicMock(spec=DiagnosticPackPort)
    mock_pack_gen.generate = MagicMock(return_value=pack)

    publisher = InMemoryInvestigationPublisher()

    service = InvestigationService(
        repository=mock_repo,
        evidence_collector=mock_collector,
        root_cause_analyzer=mock_analyzer,
        diagnostic_pack_generator=mock_pack_gen,
        publisher=publisher,
    )

    trigger = {
        "event_type": "health_check",
        "component_type": "backend",
        "component_name": "api",
        "status": "critical",
        "message": "api is down",
    }

    result = asyncio.get_event_loop().run_until_complete(service.investigate(trigger))

    assert result.status == InvestigationStatus.COMPLETED.value
    assert result.incident_id
    assert result.root_cause is not None
    assert result.evidence_bundle is not None
    assert mock_repo.save.called
    assert mock_collector.collect_evidence.called
    assert mock_analyzer.analyze.called
    assert mock_analyzer.recommend_recovery.called
    assert mock_pack_gen.generate.called
    assert len(publisher.events) >= 2  # IncidentDetected + InvestigationCompleted


def test_investigation_service_unknown_root_cause() -> None:
    incident = _incident()
    bundle = _bundle(_evidence("everything fine"))
    unknown_root_cause = RootCause(
        incident_id=incident.incident_id,
        category=RootCauseCategory.UNKNOWN,
        description="no match",
        confidence=ConfidenceScore(value=0.1),
        rule_matched="none",
    )
    recovery = RecoveryRecommendation(
        action=RecommendedAction.INVESTIGATE_MANUALLY,
        description="manual investigation",
        confidence=ConfidenceScore(value=0.3),
        estimated_impact="Unknown",
    )
    pack = DiagnosticPack(
        incident_id=incident.incident_id,
        summary="unknown pack",
        root_cause=unknown_root_cause,
        confidence_score=ConfidenceScore(value=0.1),
        recovery_recommendation=recovery,
    )

    mock_repo = AsyncMock()
    mock_collector = AsyncMock(spec=EvidenceCollectorPort)
    mock_collector.collect_evidence = AsyncMock(return_value=bundle)
    mock_analyzer = MagicMock(spec=RootCauseAnalysisPort)
    mock_analyzer.analyze = MagicMock(return_value=unknown_root_cause)
    mock_analyzer.recommend_recovery = MagicMock(return_value=recovery)
    mock_pack_gen = MagicMock(spec=DiagnosticPackPort)
    mock_pack_gen.generate = MagicMock(return_value=pack)

    service = InvestigationService(
        repository=mock_repo,
        evidence_collector=mock_collector,
        root_cause_analyzer=mock_analyzer,
        diagnostic_pack_generator=mock_pack_gen,
    )

    trigger = {
        "event_type": "health_check",
        "component_type": "backend",
        "component_name": "api",
        "status": "critical",
        "message": "something happened",
    }

    result = asyncio.get_event_loop().run_until_complete(service.investigate(trigger))
    assert result.status == InvestigationStatus.COMPLETED.value
    assert result.root_cause is not None
    assert result.root_cause.category == RootCauseCategory.UNKNOWN.value


def test_investigation_service_failure_path() -> None:
    mock_repo = AsyncMock()
    mock_collector = AsyncMock(spec=EvidenceCollectorPort)
    mock_collector.collect_evidence = AsyncMock(side_effect=RuntimeError("boom"))
    mock_analyzer = MagicMock(spec=RootCauseAnalysisPort)
    mock_pack_gen = MagicMock(spec=DiagnosticPackPort)

    service = InvestigationService(
        repository=mock_repo,
        evidence_collector=mock_collector,
        root_cause_analyzer=mock_analyzer,
        diagnostic_pack_generator=mock_pack_gen,
    )

    trigger = {
        "event_type": "health_check",
        "component_type": "backend",
        "component_name": "api",
        "status": "critical",
        "message": "something",
    }

    result = asyncio.get_event_loop().run_until_complete(service.investigate(trigger))
    assert result.status == InvestigationStatus.FAILED.value
    assert len(result.errors) == 1
    assert "boom" in result.errors[0]


def test_investigation_service_creates_incident_with_correct_fields() -> None:
    mock_repo = AsyncMock()
    bundle = _bundle()
    mock_collector = AsyncMock(spec=EvidenceCollectorPort)
    mock_collector.collect_evidence = AsyncMock(return_value=bundle)
    root_cause = _root_cause()
    recovery = _recovery()
    pack = DiagnosticPack(
        incident_id="fake",
        summary="pack",
        root_cause=root_cause,
        confidence_score=ConfidenceScore(value=0.95),
        recovery_recommendation=recovery,
    )

    mock_analyzer = MagicMock(spec=RootCauseAnalysisPort)
    mock_analyzer.analyze = MagicMock(return_value=root_cause)
    mock_analyzer.recommend_recovery = MagicMock(return_value=recovery)
    mock_pack_gen = MagicMock(spec=DiagnosticPackPort)
    mock_pack_gen.generate = MagicMock(return_value=pack)

    service = InvestigationService(
        repository=mock_repo,
        evidence_collector=mock_collector,
        root_cause_analyzer=mock_analyzer,
        diagnostic_pack_generator=mock_pack_gen,
    )

    trigger = {
        "event_type": "health_check",
        "component_type": "backend",
        "component_name": "api",
        "status": "offline",
        "message": "api offline",
    }

    asyncio.get_event_loop().run_until_complete(service.investigate(trigger))

    # Check that repository.save was called with an incident with correct fields
    save_calls = mock_repo.save.call_args_list
    first_incident = save_calls[0][0][0]  # first call, first positional arg
    assert first_incident.component_type == "backend"
    assert first_incident.component_name == "api"
    assert first_incident.severity == IncidentSeverity.EMERGENCY.value
    assert first_incident.status == IncidentStatus.DETECTED.value
    assert first_incident.triggered_by_event == "health_check"
    assert first_incident.triggered_by_component == "api"


def test_investigation_service_severity_mapping() -> None:
    """Test that severity is correctly mapped from status strings."""
    mock_repo = AsyncMock()
    bundle = _bundle()
    mock_collector = AsyncMock(spec=EvidenceCollectorPort)
    mock_collector.collect_evidence = AsyncMock(return_value=bundle)
    root_cause = _root_cause()
    recovery = _recovery()
    pack = DiagnosticPack(
        incident_id="fake",
        summary="pack",
        root_cause=root_cause,
        confidence_score=ConfidenceScore(value=0.5),
        recovery_recommendation=recovery,
    )
    mock_analyzer = MagicMock(spec=RootCauseAnalysisPort)
    mock_analyzer.analyze = MagicMock(return_value=root_cause)
    mock_analyzer.recommend_recovery = MagicMock(return_value=recovery)
    mock_pack_gen = MagicMock(spec=DiagnosticPackPort)
    mock_pack_gen.generate = MagicMock(return_value=pack)

    service = InvestigationService(
        repository=mock_repo,
        evidence_collector=mock_collector,
        root_cause_analyzer=mock_analyzer,
        diagnostic_pack_generator=mock_pack_gen,
    )

    for status, expected_severity in [
        ("critical", IncidentSeverity.CRITICAL.value),
        ("offline", IncidentSeverity.EMERGENCY.value),
        ("warning", IncidentSeverity.WARNING.value),
        ("degraded", IncidentSeverity.HIGH.value),
        ("unknown_hint", IncidentSeverity.HIGH.value),
    ]:
        mock_repo.reset_mock()
        trigger = {
            "event_type": "health_check",
            "component_type": "backend",
            "component_name": "api",
            "status": status,
            "message": "test",
        }
        asyncio.get_event_loop().run_until_complete(service.investigate(trigger))
        incident = mock_repo.save.call_args_list[0][0][0]
        assert incident.severity == expected_severity, f"status={status}"
