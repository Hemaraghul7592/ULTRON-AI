from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from app.core.database import get_session
from app.operations.incidents.domain.enums import IncidentSeverity
from app.operations.incidents.domain.models import Incident
from app.operations.incidents.infrastructure.repositories import (
    SQLAlchemyIncidentRepositoryV3,
)

if TYPE_CHECKING:
    from httpx import AsyncClient


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


@pytest.mark.asyncio
async def test_list_incidents_empty(client: AsyncClient, auth_headers: dict) -> None:
    r = await client.get("/api/v1/operations/incidents", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["incidents"] == []
    assert data["count"] == 0


@pytest.mark.asyncio
async def test_list_active_incidents_empty(
    client: AsyncClient, auth_headers: dict
) -> None:
    r = await client.get("/api/v1/operations/incidents/active", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["incidents"] == []
    assert data["count"] == 0


@pytest.mark.asyncio
async def test_list_incident_history_empty(
    client: AsyncClient, auth_headers: dict
) -> None:
    r = await client.get("/api/v1/operations/incidents/history", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["incidents"] == []


@pytest.mark.asyncio
async def test_get_incident_not_found(client: AsyncClient, auth_headers: dict) -> None:
    r = await client.get(
        "/api/v1/operations/incidents/nonexistent-id", headers=auth_headers
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_get_incident_evidence_not_found(
    client: AsyncClient, auth_headers: dict
) -> None:
    r = await client.get(
        "/api/v1/operations/incidents/nonexistent-id/evidence", headers=auth_headers
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_get_incident_diagnostics_not_found(
    client: AsyncClient, auth_headers: dict
) -> None:
    r = await client.get(
        "/api/v1/operations/incidents/nonexistent-id/diagnostics",
        headers=auth_headers,
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_list_incidents_with_data(client: AsyncClient, auth_headers: dict) -> None:
    async with get_session()() as session:
        repo = SQLAlchemyIncidentRepositoryV3(session)
        inc = _incident()
        await repo.save(inc)
        await session.commit()

    r = await client.get("/api/v1/operations/incidents", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert len(data["incidents"]) >= 1
    ids = [i["incident_id"] for i in data["incidents"]]
    assert inc.incident_id in ids


@pytest.mark.asyncio
async def test_get_incident_by_id(client: AsyncClient, auth_headers: dict) -> None:
    async with get_session()() as session:
        repo = SQLAlchemyIncidentRepositoryV3(session)
        inc = _incident()
        await repo.save(inc)
        await session.commit()

    r = await client.get(
        f"/api/v1/operations/incidents/{inc.incident_id}", headers=auth_headers
    )
    assert r.status_code == 200
    data = r.json()
    assert data["incident"]["incident_id"] == inc.incident_id
    assert data["incident"]["component_name"] == "api"
    assert data["evidence_count"] == 0


@pytest.mark.asyncio
async def test_investigate_endpoint(client: AsyncClient, auth_headers: dict) -> None:
    r = await client.post(
        "/api/v1/operations/investigate",
        headers=auth_headers,
        json={
            "component_type": "backend",
            "component_name": "api",
            "environment": "production",
            "message": "api is down",
            "status": "critical",
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["incident_id"]
    assert data["status"]
    assert data["evidence_count"] >= 0
    assert isinstance(data["errors"], list)


@pytest.mark.asyncio
async def test_investigate_creates_incident_in_db(
    client: AsyncClient, auth_headers: dict
) -> None:
    r = await client.post(
        "/api/v1/operations/investigate",
        headers=auth_headers,
        json={
            "component_type": "backend",
            "component_name": "api",
            "environment": "production",
            "message": "api down",
            "status": "critical",
        },
    )
    assert r.status_code == 200
    incident_id = r.json()["incident_id"]

    # Verify incident was persisted
    r2 = await client.get(
        f"/api/v1/operations/incidents/{incident_id}", headers=auth_headers
    )
    assert r2.status_code == 200
    assert r2.json()["incident"]["incident_id"] == incident_id


@pytest.mark.asyncio
async def test_list_active_incidents_with_data(
    client: AsyncClient, auth_headers: dict
) -> None:
    async with get_session()() as session:
        repo = SQLAlchemyIncidentRepositoryV3(session)
        inc = _incident()
        await repo.save(inc)
        await session.commit()

    r = await client.get("/api/v1/operations/incidents/active", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert len(data["incidents"]) >= 1


@pytest.mark.asyncio
async def test_incident_detail_with_evidence(
    client: AsyncClient, auth_headers: dict
) -> None:
    async with get_session()() as session:
        repo = SQLAlchemyIncidentRepositoryV3(session)
        inc = _incident()
        await repo.save(inc)

        from app.operations.incidents.domain.enums import EvidenceCategory
        from app.operations.incidents.domain.models import IncidentEvidence

        evidence = IncidentEvidence(
            incident_id=inc.incident_id,
            category=EvidenceCategory.LOG,
            source="test_log",
            payload_ref="ref",
            redacted_excerpt="error in logs",
            checksum="d" * 32,
        )
        await repo.add_evidence(inc.incident_id, [evidence])
        await session.commit()

    r = await client.get(
        f"/api/v1/operations/incidents/{inc.incident_id}", headers=auth_headers
    )
    assert r.status_code == 200
    data = r.json()
    assert data["evidence_count"] == 1


@pytest.mark.asyncio
async def test_get_incident_evidence_with_data(
    client: AsyncClient, auth_headers: dict
) -> None:
    async with get_session()() as session:
        repo = SQLAlchemyIncidentRepositoryV3(session)
        inc = _incident()
        await repo.save(inc)

        from app.operations.incidents.domain.enums import EvidenceCategory
        from app.operations.incidents.domain.models import IncidentEvidence

        evidence = IncidentEvidence(
            incident_id=inc.incident_id,
            category=EvidenceCategory.METRIC,
            source="cpu_monitor",
            payload_ref="ref",
            redacted_excerpt="cpu at 95%",
            checksum="e" * 32,
        )
        await repo.add_evidence(inc.incident_id, [evidence])
        await session.commit()

    r = await client.get(
        f"/api/v1/operations/incidents/{inc.incident_id}/evidence",
        headers=auth_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["count"] == 1
    assert data["evidence"][0]["source"] == "cpu_monitor"


@pytest.mark.asyncio
async def test_incidents_endpoint_compatible_with_sprint2(
    client: AsyncClient, auth_headers: dict
) -> None:
    """Verify the response shape is compatible with Sprint 2 tests."""
    r = await client.get("/api/v1/operations/incidents", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert "incidents" in data
    assert isinstance(data["incidents"], list)
