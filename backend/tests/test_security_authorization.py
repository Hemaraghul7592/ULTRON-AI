from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from httpx import AsyncClient

from app.core.config import get_settings
from app.core.logging import sanitize_event_dict
from app.core.security import create_access_token


async def _register(client: AsyncClient, username: str) -> dict[str, str]:
    response = await client.post(
        "/api/v1/auth/register",
        json={"username": username, "password": "TestPass123!"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.mark.asyncio
async def test_conversation_access_is_scoped_to_authenticated_user(client: AsyncClient):
    first = await _register(client, f"first_{uuid.uuid4().hex[:8]}")
    second = await _register(client, f"second_{uuid.uuid4().hex[:8]}")

    created = await client.post("/api/v1/conversations", json={}, headers=first)
    assert created.status_code == 201
    conversation_id = created.json()["id"]

    response = await client.get(f"/api/v1/conversations/{conversation_id}", headers=second)
    assert response.status_code == 404

    response = await client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        json={"content": "cross-user"},
        headers=second,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_chat_rejects_cross_user_conversation(client: AsyncClient):
    first = await _register(client, f"owner_{uuid.uuid4().hex[:8]}")
    second = await _register(client, f"caller_{uuid.uuid4().hex[:8]}")
    created = await client.post("/api/v1/conversations", json={}, headers=first)
    conversation_id = created.json()["id"]

    response = await client.post(
        "/api/v1/chat",
        json={"message": "read it", "conversation_id": conversation_id},
        headers=second,
    )
    assert response.status_code == 400, response.text
    assert response.json()["error_code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_tool_execution_requires_authentication_and_rejects_identity_override(
    client: AsyncClient,
):
    response = await client.post(
        "/api/v1/tools/execute",
        json={"name": "search_google_drive", "arguments": {"user_id": "other"}},
    )
    assert response.status_code == 401

    headers = await _register(client, f"tool_{uuid.uuid4().hex[:8]}")
    response = await client.post(
        "/api/v1/tools/execute",
        json={"name": "search_google_drive", "arguments": {"user_id": "other"}},
        headers=headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_metrics_require_admin_role(client: AsyncClient):
    response = await client.get("/api/v1/observability/metrics")
    assert response.status_code == 401

    headers = await _register(client, f"metrics_{uuid.uuid4().hex[:8]}")
    response = await client.get("/api/v1/observability/metrics", headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_metrics_are_available_to_configured_admin(client: AsyncClient):
    admin_id = str(uuid.uuid4())
    get_settings().ADMIN_USER_IDS.append(admin_id)
    token = create_access_token({"user_id": admin_id, "sub": "admin", "role": "admin"})

    response = await client.get(
        "/api/v1/observability/metrics",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200


def test_logging_redacts_sensitive_and_nested_values():
    event = sanitize_event_dict(
        None,  # type: ignore[arg-type]
        "info",
        {
            "authorization": "Bearer secret-token",
            "prompt": "private conversation content",
            "nested": {"api_key": "key-value", "safe": "ok"},
            "error": "request failed with password=hunter2",
        },
    )

    assert event["authorization"] == "***REDACTED***"
    assert event["prompt"] == "***REDACTED***"
    assert event["nested"]["api_key"] == "***REDACTED***"
    assert "hunter2" not in event["error"]


@pytest.mark.asyncio
async def test_invalid_ids_and_pagination_return_validation_errors(client: AsyncClient):
    headers = await _register(client, f"validation_{uuid.uuid4().hex[:8]}")
    invalid_id = "x" * 37

    response = await client.get(f"/api/v1/conversations/{invalid_id}", headers=headers)
    assert response.status_code == 422

    response = await client.get(
        "/api/v1/observability/metrics?limit=0",
        headers={"Authorization": "Bearer invalid"},
    )
    assert response.status_code == 401

    response = await client.get("/api/v1/memory?page=0", headers=headers)
    assert response.status_code == 422
