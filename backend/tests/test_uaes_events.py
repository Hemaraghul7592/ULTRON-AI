from __future__ import annotations

import pytest

from app.operations.core.event_bus import InProcessEventBus
from app.operations.domain.enums import (
    ComponentType,
    EnvironmentType,
    EventType,
    EvidenceType,
    HealthStatus,
    IncidentSeverity,
)
from app.operations.domain.events import EvidenceCollected, HealthSnapshotRecorded, IncidentCreated
from app.operations.domain.models import ComponentHealth, EvidenceItem, HealthSnapshot, Incident
from app.operations.domain.value_objects import ConfidenceScore


@pytest.mark.asyncio
async def test_event_bus_publish_subscribe_and_unsubscribe() -> None:
    bus = InProcessEventBus()
    events: list[tuple[str, str]] = []

    async def first_handler(event: HealthSnapshotRecorded) -> None:
        events.append(("first", event.event_type))

    async def second_handler(event: HealthSnapshotRecorded) -> None:
        events.append(("second", event.event_type))

    subscription = bus.subscribe(HealthSnapshotRecorded, first_handler)
    bus.subscribe(HealthSnapshotRecorded, second_handler)

    snapshot = HealthSnapshot(
        snapshot_id="snapshot-1",
        environment=EnvironmentType.PRODUCTION,
        overall_status=HealthStatus.WARNING,
        overall_score=82.5,
        components=(
            ComponentHealth(
                component_id="backend",
                component_type=ComponentType.BACKEND,
                component_name="backend",
                environment=EnvironmentType.PRODUCTION,
                status=HealthStatus.WARNING,
                score=82.5,
                message="degraded",
            ),
        ),
    )

    await bus.publish(HealthSnapshotRecorded(snapshot=snapshot))
    assert events == [
        ("first", EventType.HEALTH_SNAPSHOT_RECORDED.value),
        ("second", EventType.HEALTH_SNAPSHOT_RECORDED.value),
    ]

    bus.unsubscribe(subscription)
    events.clear()
    await bus.publish(HealthSnapshotRecorded(snapshot=snapshot))
    assert events == [("second", EventType.HEALTH_SNAPSHOT_RECORDED.value)]


def test_domain_events_serialize_to_dict() -> None:
    evidence = EvidenceItem(
        evidence_id="evidence-1",
        incident_id="incident-1",
        evidence_type=EvidenceType.FASTAPI_LOG,
        source="app",
        payload_ref="logs/1",
        redacted_excerpt="traceback omitted",
        checksum="abcd1234",
    )
    incident = Incident(
        incident_id="incident-1",
        severity=IncidentSeverity.HIGH,
        component=ComponentType.BACKEND,
        environment=EnvironmentType.PRODUCTION,
        summary="API outage",
        detailed_description="Backend returned 500 for health checks.",
        evidence=[evidence],
        confidence=ConfidenceScore(value=0.88),
    )
    event = IncidentCreated(incident=incident)
    payload = event.to_dict()
    assert payload["event_type"] == EventType.INCIDENT_CREATED.value
    assert payload["incident"]["summary"] == "API outage"

    restored = EvidenceCollected.model_validate(
        {
            "event_type": EventType.EVIDENCE_COLLECTED,
            "event_id": "event-1",
            "occurred_at": "2026-08-03T00:00:00Z",
            "source": "uaes",
            "evidence": evidence.to_dict(),
        },
    )
    assert restored.evidence.redacted_excerpt == "traceback omitted"
