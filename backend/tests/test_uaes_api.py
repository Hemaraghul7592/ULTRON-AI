from __future__ import annotations

import asyncio

import pytest  # noqa: TC002
from httpx import AsyncClient  # noqa: TC002


@pytest.mark.asyncio
async def test_operations_endpoints_return_collections(
    client: AsyncClient, auth_headers: dict,
) -> None:
    responses = await asyncio.gather(
        client.get("/api/v1/operations/health", headers=auth_headers),
        client.get("/api/v1/operations/incidents", headers=auth_headers),
        client.get("/api/v1/operations/metrics", headers=auth_headers),
        client.get("/api/v1/operations/diagnostics", headers=auth_headers),
    )
    health, incidents, metrics, diagnostics = responses

    assert health.status_code == 200
    assert incidents.status_code == 200
    assert metrics.status_code == 200
    assert diagnostics.status_code == 200

    assert health.json()["snapshots"] == []
    assert incidents.json()["incidents"] == []
    assert metrics.json()["metrics"] == []
    assert diagnostics.json()["diagnostic_packs"] == []
