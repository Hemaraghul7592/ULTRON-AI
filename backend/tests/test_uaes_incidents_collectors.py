from __future__ import annotations

import asyncio

import pytest

from app.operations.incidents.domain.enums import EvidenceCategory, IncidentSeverity
from app.operations.incidents.domain.models import Incident
from app.operations.incidents.infrastructure.collectors.base import (
    BaseCollector,
    EvidenceCollector,
    _build_error_evidence,
    _build_evidence,
    _make_checksum,
    _make_evidence_id,
    _make_excerpt,
)
from app.operations.incidents.infrastructure.collectors.config_collectors import (
    ConfigCollector,
    EnvironmentVariableCollector,
    HealthSnapshotCollector,
    MetricsSnapshotCollector,
    StartupSequenceCollector,
)
from app.operations.incidents.infrastructure.collectors.factory import create_default_collectors
from app.operations.incidents.infrastructure.collectors.log_collectors import (
    FastAPILogCollector,
    SchedulerLogCollector,
    StackTraceCollector,
    StructuredLogCollector,
)
from app.operations.incidents.infrastructure.collectors.system_collectors import (
    CpuStatusCollector,
    DatabaseStatusCollector,
    DiskStatusCollector,
    DiStateCollector,
    DockerStatusCollector,
    MemoryStatusCollector,
    NetworkStatusCollector,
    RedisStatusCollector,
    RunningTasksCollector,
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


def test_make_evidence_id_is_string() -> None:
    eid = _make_evidence_id()
    assert isinstance(eid, str)
    assert len(eid) == 36


def test_make_checksum_deterministic() -> None:
    assert _make_checksum("hello") == _make_checksum("hello")
    assert _make_checksum("hello") != _make_checksum("world")


def test_make_excerpt_short_text() -> None:
    assert _make_excerpt("short") == "short"


def test_make_excerpt_long_text() -> None:
    long = "x" * 3000
    result = _make_excerpt(long, max_len=2000)
    assert len(result) == 2014
    assert result.endswith("...(truncated)")
    assert result[:2000] == "x" * 2000


def test_build_evidence_fields() -> None:
    incident = _incident()
    evidence = _build_evidence(incident, EvidenceCategory.LOG, "source", "ref", "content")
    assert evidence.incident_id == incident.incident_id
    assert evidence.category == EvidenceCategory.LOG.value
    assert evidence.source == "source"
    assert evidence.payload_ref == "ref"
    assert evidence.redacted_excerpt == "content"
    assert evidence.checksum
    assert evidence.metadata == {}


def test_build_evidence_with_metadata() -> None:
    incident = _incident()
    evidence = _build_evidence(
        incident, EvidenceCategory.LOG, "source", "ref", "content", {"k": "v"}
    )
    assert evidence.metadata == {"k": "v"}


def test_build_error_evidence() -> None:
    incident = _incident()
    evidence = _build_error_evidence(incident, "test_collector", "something broke")
    assert evidence.category == EvidenceCategory.SYSTEM.value
    assert evidence.source == "test_collector"
    assert "Collection failed" in evidence.redacted_excerpt
    # type("something broke").__name__ == "str"
    assert evidence.metadata["error_type"] == "str"


def test_base_collector_collect_raises() -> None:
    collector = BaseCollector()
    with pytest.raises(NotImplementedError):
        asyncio.get_event_loop().run_until_complete(collector.collect(_incident()))


def test_base_collector_collect_error() -> None:
    collector = BaseCollector()
    evidence = asyncio.get_event_loop().run_until_complete(
        collector.collect_error(_incident(), "error msg")
    )
    assert evidence.category == EvidenceCategory.SYSTEM.value
    assert "Collection failed" in evidence.redacted_excerpt


def test_evidence_collector_protocol() -> None:
    assert isinstance(BaseCollector(), EvidenceCollector)


def test_fastapi_log_collector_no_log_file() -> None:
    collector = FastAPILogCollector(log_path="/nonexistent/path")
    incident = _incident()
    evidence = asyncio.get_event_loop().run_until_complete(collector.collect(incident))
    assert evidence.redacted_excerpt == "FastAPI log file not found"


def test_stack_trace_collector_empty() -> None:
    collector = StackTraceCollector()
    incident = _incident()
    evidence = asyncio.get_event_loop().run_until_complete(collector.collect(incident))
    assert "No stack traces captured" in evidence.redacted_excerpt


def test_stack_trace_collector_with_capture() -> None:
    collector = StackTraceCollector()
    try:
        raise ValueError("test error")
    except ValueError as e:
        collector.capture(e, context="test")
    incident = _incident()
    evidence = asyncio.get_event_loop().run_until_complete(collector.collect(incident))
    assert "ValueError" in evidence.redacted_excerpt
    assert "test error" in evidence.redacted_excerpt


def test_structured_log_collector_empty() -> None:
    collector = StructuredLogCollector()
    incident = _incident()
    evidence = asyncio.get_event_loop().run_until_complete(collector.collect(incident))
    assert "No structured log entries captured" in evidence.redacted_excerpt


def test_scheduler_log_collector_empty() -> None:
    collector = SchedulerLogCollector()
    incident = _incident()
    evidence = asyncio.get_event_loop().run_until_complete(collector.collect(incident))
    assert "No scheduler log entries captured" in evidence.redacted_excerpt


def test_health_snapshot_collector_no_snapshot() -> None:
    collector = HealthSnapshotCollector()
    incident = _incident()
    evidence = asyncio.get_event_loop().run_until_complete(collector.collect(incident))
    assert "No health snapshot available" in evidence.redacted_excerpt


def test_metrics_snapshot_collector_no_metrics() -> None:
    collector = MetricsSnapshotCollector()
    incident = _incident()
    evidence = asyncio.get_event_loop().run_until_complete(collector.collect(incident))
    assert "No metrics snapshot available" in evidence.redacted_excerpt


def test_environment_variable_collector() -> None:
    collector = EnvironmentVariableCollector()
    incident = _incident()
    evidence = asyncio.get_event_loop().run_until_complete(collector.collect(incident))
    assert evidence.redacted_excerpt  # should contain env vars


def test_config_collector_no_config() -> None:
    collector = ConfigCollector()
    incident = _incident()
    evidence = asyncio.get_event_loop().run_until_complete(collector.collect(incident))
    assert evidence.redacted_excerpt  # should contain empty or default config


def test_startup_sequence_collector_empty() -> None:
    collector = StartupSequenceCollector()
    incident = _incident()
    evidence = asyncio.get_event_loop().run_until_complete(collector.collect(incident))
    assert "No startup sequence recorded" in evidence.redacted_excerpt


def test_docker_status_collector() -> None:
    collector = DockerStatusCollector()
    incident = _incident()
    evidence = asyncio.get_event_loop().run_until_complete(collector.collect(incident))
    assert evidence.category == EvidenceCategory.SYSTEM.value


def test_database_status_collector() -> None:
    collector = DatabaseStatusCollector()
    incident = _incident()
    evidence = asyncio.get_event_loop().run_until_complete(collector.collect(incident))
    assert evidence.category == EvidenceCategory.SYSTEM.value


def test_redis_status_collector() -> None:
    collector = RedisStatusCollector()
    incident = _incident()
    evidence = asyncio.get_event_loop().run_until_complete(collector.collect(incident))
    assert evidence.category == EvidenceCategory.SYSTEM.value


def test_cpu_status_collector() -> None:
    collector = CpuStatusCollector()
    incident = _incident()
    evidence = asyncio.get_event_loop().run_until_complete(collector.collect(incident))
    assert evidence.category == EvidenceCategory.METRIC.value


def test_memory_status_collector() -> None:
    collector = MemoryStatusCollector()
    incident = _incident()
    evidence = asyncio.get_event_loop().run_until_complete(collector.collect(incident))
    assert evidence.category == EvidenceCategory.METRIC.value


def test_disk_status_collector() -> None:
    collector = DiskStatusCollector()
    incident = _incident()
    evidence = asyncio.get_event_loop().run_until_complete(collector.collect(incident))
    assert evidence.category == EvidenceCategory.METRIC.value


def test_network_status_collector() -> None:
    collector = NetworkStatusCollector()
    incident = _incident()
    evidence = asyncio.get_event_loop().run_until_complete(collector.collect(incident))
    assert evidence.category == EvidenceCategory.SYSTEM.value


def test_running_tasks_collector() -> None:
    collector = RunningTasksCollector()
    incident = _incident()
    evidence = asyncio.get_event_loop().run_until_complete(collector.collect(incident))
    assert evidence.category == EvidenceCategory.STATE.value


def test_di_state_collector() -> None:
    collector = DiStateCollector()
    incident = _incident()
    evidence = asyncio.get_event_loop().run_until_complete(collector.collect(incident))
    assert evidence.category == EvidenceCategory.STATE.value


def test_create_default_collectors_returns_21() -> None:
    collectors = create_default_collectors()
    assert len(collectors) == 21
    names = {c.name for c in collectors}
    assert "fastapi_logs" in names
    assert "docker_status" in names
    assert "git_commit" in names
    assert "stack_traces" in names
