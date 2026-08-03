from __future__ import annotations

import pytest

from app.core.database import get_session
from app.operations.domain.enums import (
    ComponentType,
    EnvironmentType,
    EvidenceType,
    HealthStatus,
    IncidentSeverity,
    IncidentStatus,
    MetricType,
)
from app.operations.domain.events import HealthSnapshotRecorded
from app.operations.domain.models import (
    ComponentHealth,
    DiagnosticPack,
    EvidenceItem,
    HealthSnapshot,
    Incident,
    MetricSample,
)
from app.operations.domain.value_objects import ConfidenceScore
from app.operations.infrastructure.db.repositories import (
    SQLAlchemyDiagnosticRepository,
    SQLAlchemyEventRepository,
    SQLAlchemyHealthRepository,
    SQLAlchemyIncidentRepository,
    SQLAlchemyMetricsRepository,
)


@pytest.mark.asyncio
async def test_repository_round_trips() -> None:
    session_factory = get_session()
    async with session_factory() as session:
        health_repo = SQLAlchemyHealthRepository(session)
        incident_repo = SQLAlchemyIncidentRepository(session)
        metrics_repo = SQLAlchemyMetricsRepository(session)
        diagnostic_repo = SQLAlchemyDiagnosticRepository(session)
        event_repo = SQLAlchemyEventRepository(session)

        snapshot = HealthSnapshot(
            snapshot_id="snapshot-1",
            environment=EnvironmentType.STAGING,
            overall_status=HealthStatus.WARNING,
            overall_score=80.0,
            components=[
                ComponentHealth(
                    component_id="backend",
                    component_type=ComponentType.BACKEND,
                    component_name="backend",
                    environment=EnvironmentType.STAGING,
                    status=HealthStatus.WARNING,
                    score=80.0,
                    message="degraded",
                    details={"latency_ms": "180"},
                ),
            ],
        )
        stored_snapshot = await health_repo.record_snapshot(snapshot)
        assert stored_snapshot.snapshot_id == "snapshot-1"

        incident = Incident(
            incident_id="incident-1",
            severity=IncidentSeverity.CRITICAL,
            component=ComponentType.DATABASE,
            environment=EnvironmentType.PRODUCTION,
            summary="Database unavailable",
            detailed_description="Read queries failed.",
            evidence=[
                EvidenceItem(
                    evidence_id="evidence-1",
                    incident_id="incident-1",
                    evidence_type=EvidenceType.SYSTEM_LOG,
                    source="system",
                    payload_ref="/var/log/system.log",
                    redacted_excerpt="db timeout",
                    checksum="checksum-1",
                ),
            ],
            status=IncidentStatus.OPEN,
            confidence=ConfidenceScore(value=0.93),
        )
        stored_incident = await incident_repo.create(incident)
        assert stored_incident.incident_id == "incident-1"
        resolved = await incident_repo.resolve("incident-1", "Database restarted")
        assert resolved is not None
        assert resolved.status == IncidentStatus.RESOLVED.value

        metric = MetricSample(
            metric_id="metric-1",
            metric_type=MetricType.CPU_PERCENT,
            name="cpu_percent",
            value=72.4,
            unit="percent",
            environment=EnvironmentType.PRODUCTION,
            source="system",
            tags={"host": "backend-1"},
        )
        stored_metrics = await metrics_repo.record([metric])
        assert stored_metrics[0].metric_id == "metric-1"

        pack = DiagnosticPack(
            pack_id="pack-1",
            incident_id="incident-1",
            summary="Diagnostics captured",
            log_ref="logs/incident-1",
            evidence=[incident.evidence[0]],
        )
        stored_pack = await diagnostic_repo.create(pack)
        assert stored_pack.pack_id == "pack-1"

        event = HealthSnapshotRecorded(snapshot=snapshot)
        stored_event = await event_repo.append(event)
        assert stored_event.event_id == event.event_id

        snapshots = await health_repo.list_snapshots()
        incidents = await incident_repo.list_history()
        metrics = await metrics_repo.list_recent()
        diagnostics = await diagnostic_repo.list_recent()
        events = await event_repo.list_recent()

        assert len(snapshots) == 1
        assert len(incidents) == 1
        assert len(metrics) == 1
        assert len(diagnostics) == 1
        assert len(events) == 1
