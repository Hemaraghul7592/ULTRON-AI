import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_public(client: AsyncClient):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] in ("healthy", "degraded")


@pytest.mark.asyncio
async def test_root_public(client: AsyncClient):
    r = await client.get("/")
    assert r.status_code == 200
    assert r.json()["name"] == "ULTRON"


@pytest.mark.asyncio
async def test_register_and_login(client: AsyncClient):
    r = await client.post("/api/v1/auth/register", json={"username": "testuser", "password": "TestPass123!"})
    assert r.status_code == 200, f"register: {r.status_code} {r.text}"
    data = r.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    r = await client.post("/api/v1/auth/login", json={"username": "testuser", "password": "TestPass123!"})
    assert r.status_code == 200, f"login: {r.status_code} {r.text}"
    data = r.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_protected_routes_return_401_without_token(client: AsyncClient):
    routes = [
        ("GET", "/api/v1/conversations"),
        ("POST", "/api/v1/chat", {"message": "hi"}),
        ("GET", "/api/v1/memory"),
        ("POST", "/api/v1/memory", {"content": "test"}),
        ("GET", "/api/v1/tasks"),
        ("GET", "/api/v1/entities"),
        ("GET", "/api/v1/tools"),
        ("POST", "/api/v1/tools/execute", {"name": "test"}),
        ("POST", "/api/v1/voice/stt", {"audio_base64": "dGVzdA=="}),
        ("GET", "/api/v1/observability/metrics"),
    ]
    for method, path, *body in routes:
        if method == "GET":
            r = await client.get(path)
        else:
            r = await client.post(path, json=body[0] if body else {})
        assert r.status_code == 401, f"{method} {path}: expected 401 got {r.status_code}"


@pytest.mark.asyncio
async def test_protected_routes_work_with_valid_jwt(client: AsyncClient):
    r = await client.post("/api/v1/auth/register", json={"username": "testuser", "password": "TestPass123!"})
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    r = await client.get("/api/v1/conversations", headers=headers)
    assert r.status_code == 200, f"conversations: {r.status_code}"

    r = await client.get("/api/v1/auth/verify", headers=headers)
    assert r.status_code == 200

    r = await client.get("/api/v1/memory", headers=headers)
    assert r.status_code == 200

    r = await client.get("/api/v1/tasks", headers=headers)
    assert r.status_code == 200

    r = await client.get("/api/v1/entities", headers=headers)
    assert r.status_code == 200

    r = await client.get("/api/v1/tools", headers=headers)
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_invalid_jwt_rejected(client: AsyncClient):
    r = await client.get("/api/v1/conversations", headers={"Authorization": "Bearer invalid-token"})
    assert r.status_code == 401

    r = await client.get("/api/v1/conversations", headers={"Authorization": "Bearer x.y.z"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_missing_jwt_rejected(client: AsyncClient):
    r = await client.get("/api/v1/conversations")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_duplicate_registration_returns_409(client: AsyncClient):
    payload = {"username": "duptest", "password": "TestPass123!"}
    r = await client.post("/api/v1/auth/register", json=payload)
    assert r.status_code == 200

    r = await client.post("/api/v1/auth/register", json=payload)
    assert r.status_code == 409
    data = r.json()
    assert "Username already exists" in data.get("detail", "")
