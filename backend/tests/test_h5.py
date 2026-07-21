import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_enhanced(client: AsyncClient):
    r = await client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] in ("healthy", "degraded")
    assert "version" in data
    assert "checks" in data
    assert "database" in data["checks"]
    assert "redis" in data["checks"]


@pytest.mark.asyncio
async def test_health_db_check(client: AsyncClient):
    r = await client.get("/health")
    data = r.json()
    assert data["checks"]["database"]["status"] == "healthy"


@pytest.mark.asyncio
async def test_health_redis_not_configured(client: AsyncClient):
    r = await client.get("/health")
    data = r.json()
    assert data["checks"]["redis"]["status"] == "not_configured"


@pytest.mark.asyncio
async def test_conversation_list_message_count(client: AsyncClient, auth_headers: dict):
    r = await client.post("/api/v1/conversations", json={}, headers=auth_headers)
    assert r.status_code == 201

    r = await client.get("/api/v1/conversations", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert "conversations" in data
    assert "total" in data
    for conv in data["conversations"]:
        assert "message_count" in conv
        assert isinstance(conv["message_count"], int)


@pytest.mark.asyncio
async def test_voice_session_create_and_list(client: AsyncClient, auth_headers: dict):
    r = await client.post("/api/v1/voice/session/create", json={}, headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert "session_id" in data
    assert data["session_id"] != "not_initialized"

    r = await client.get("/api/v1/voice/sessions", headers=auth_headers)
    assert r.status_code == 200
    sessions = r.json()
    assert isinstance(sessions, list)
    assert any(s["session_id"] == data["session_id"] for s in sessions)


@pytest.mark.asyncio
async def test_voice_session_close(client: AsyncClient, auth_headers: dict):
    r = await client.post("/api/v1/voice/session/create", json={}, headers=auth_headers)
    assert r.status_code == 200
    session_id = r.json()["session_id"]
    assert session_id != "not_initialized"

    r = await client.delete(f"/api/v1/voice/session/{session_id}", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["closed"] is True


@pytest.mark.asyncio
async def test_tools_list(client: AsyncClient, auth_headers: dict):
    r = await client.get("/api/v1/tools", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_tools_definitions(client: AsyncClient, auth_headers: dict):
    r = await client.get("/api/v1/tools/definitions", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_tools_plugins(client: AsyncClient, auth_headers: dict):
    r = await client.get("/api/v1/tools/plugins", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert "plugins" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_user_isolation_conversations(client: AsyncClient):
    r1 = await client.post("/api/v1/auth/register", json={"username": "user_a", "password": "TestPass123!"})
    token_a = r1.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    r2 = await client.post("/api/v1/auth/register", json={"username": "user_b", "password": "TestPass123!"})
    token_b = r2.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    r = await client.post("/api/v1/conversations", json={}, headers=headers_a)
    assert r.status_code == 201

    r = await client.get("/api/v1/conversations", headers=headers_a)
    assert r.json()["total"] == 1

    r = await client.get("/api/v1/conversations", headers=headers_b)
    assert r.json()["total"] == 0


@pytest.mark.asyncio
async def test_user_isolation_memories(client: AsyncClient):
    r1 = await client.post("/api/v1/auth/register", json={"username": "user_c", "password": "TestPass123!"})
    token_c = r1.json()["access_token"]
    headers_c = {"Authorization": f"Bearer {token_c}"}

    r2 = await client.post("/api/v1/auth/register", json={"username": "user_d", "password": "TestPass123!"})
    token_d = r2.json()["access_token"]
    headers_d = {"Authorization": f"Bearer {token_d}"}

    r = await client.post("/api/v1/memory", json={"content": "user_c memory"}, headers=headers_c)
    assert r.status_code == 201

    r = await client.get("/api/v1/memory", headers=headers_c)
    assert r.json()["total"] == 1

    r = await client.get("/api/v1/memory", headers=headers_d)
    assert r.json()["total"] == 0


@pytest.mark.asyncio
async def test_user_isolation_tasks(client: AsyncClient):
    r1 = await client.post("/api/v1/auth/register", json={"username": "user_e", "password": "TestPass123!"})
    token_e = r1.json()["access_token"]
    headers_e = {"Authorization": f"Bearer {token_e}"}

    r2 = await client.post("/api/v1/auth/register", json={"username": "user_f", "password": "TestPass123!"})
    token_f = r2.json()["access_token"]
    headers_f = {"Authorization": f"Bearer {token_f}"}

    r = await client.post("/api/v1/tasks", json={"title": "user_e task"}, headers=headers_e)
    assert r.status_code == 201

    r = await client.get("/api/v1/tasks", headers=headers_e)
    assert r.json()["total"] == 1

    r = await client.get("/api/v1/tasks", headers=headers_f)
    assert r.json()["total"] == 0


@pytest.mark.asyncio
async def test_voice_stt_no_auth(client: AsyncClient):
    r = await client.post("/api/v1/voice/stt", json={"audio_base64": "dGVzdA=="})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_voice_tts_no_auth(client: AsyncClient):
    r = await client.post("/api/v1/voice/tts", json={"text": "hello"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_tools_execute_no_auth(client: AsyncClient):
    r = await client.post("/api/v1/tools/execute", json={"name": "test"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_observability_health_removed(client: AsyncClient):
    r = await client.get("/api/v1/observability/health")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_observability_metrics_no_auth(client: AsyncClient):
    r = await client.get("/api/v1/observability/metrics")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_token_usage_model(client: AsyncClient):
    from app.models.token import TokenUsage
    tu = TokenUsage(
        provider="test",
        model="test-model",
        prompt_tokens=10,
        completion_tokens=20,
        user_id="test-user",
    )
    assert tu.user_id == "test-user"


@pytest.mark.asyncio
async def test_health_public_no_auth(client: AsyncClient):
    r = await client.get("/health")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_root_public_no_auth(client: AsyncClient):
    r = await client.get("/")
    assert r.status_code == 200
    assert r.json()["name"] == "ULTRON"


@pytest.mark.asyncio
async def test_google_oauth_callback_persists_refresh_token(client: AsyncClient, auth_headers: dict):
    from datetime import timedelta

    from app.core.security import create_access_token, decode_access_token
    from app.services.google_oauth import GoogleOAuthService

    token = auth_headers["Authorization"].replace("Bearer ", "")
    payload = decode_access_token(token)
    user_id = payload["user_id"]

    test_state = create_access_token(
        data={"sub": user_id, "purpose": "oauth_state"},
        expires_delta=timedelta(minutes=10),
    )

    original = GoogleOAuthService.exchange_code

    async def mock_exchange(self, code, redirect_uri):
        return {
            "access_token": "fake-access-token",
            "refresh_token": "fake-refresh-token-value!!!!!",
            "expires_in": 3600,
            "scope": "openid email profile",
            "token_type": "Bearer",
        }

    GoogleOAuthService.exchange_code = mock_exchange

    try:
        r = await client.get(
            "/api/v1/google/auth/callback",
            params={"code": "auth_code", "state": test_state},
        )
        assert r.status_code == 200
        assert r.json()["status"] == "success"

        r = await client.get("/api/v1/google/auth/status", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert data["connected"] is True
        assert "openid" in data["scopes"]
    finally:
        GoogleOAuthService.exchange_code = original
