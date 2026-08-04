import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("healthy", "degraded")


@pytest.mark.asyncio
async def test_root(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "ULTRON"


@pytest.mark.asyncio
async def test_create_conversation(client: AsyncClient, auth_headers: dict):
    response = await client.post("/api/v1/conversations", json={}, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data


@pytest.mark.asyncio
async def test_list_conversations(client: AsyncClient, auth_headers: dict):
    response = await client.get("/api/v1/conversations", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "conversations" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_create_and_get_conversation(client: AsyncClient, auth_headers: dict):
    create_resp = await client.post("/api/v1/conversations", json={}, headers=auth_headers)
    assert create_resp.status_code == 201
    conv_id = create_resp.json()["id"]

    get_resp = await client.get(f"/api/v1/conversations/{conv_id}", headers=auth_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == conv_id


@pytest.mark.asyncio
async def test_delete_conversation(client: AsyncClient, auth_headers: dict):
    create_resp = await client.post("/api/v1/conversations", json={}, headers=auth_headers)
    conv_id = create_resp.json()["id"]

    delete_resp = await client.delete(f"/api/v1/conversations/{conv_id}", headers=auth_headers)
    assert delete_resp.status_code == 204

    get_resp = await client.get(f"/api/v1/conversations/{conv_id}", headers=auth_headers)
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_create_memory(client: AsyncClient, auth_headers: dict):
    response = await client.post(
        "/api/v1/memory",
        json={"content": "test memory"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data


@pytest.mark.asyncio
async def test_list_memories(client: AsyncClient, auth_headers: dict):
    response = await client.get("/api/v1/memory", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "memories" in data


@pytest.mark.asyncio
async def test_search_memories(client: AsyncClient, auth_headers: dict):
    response = await client.post(
        "/api/v1/memory/search",
        json={"query": "test"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "memories" in data


@pytest.mark.asyncio
async def test_create_task(client: AsyncClient, auth_headers: dict):
    response = await client.post("/api/v1/tasks", json={"title": "Test Task"}, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data


@pytest.mark.asyncio
async def test_list_tasks(client: AsyncClient, auth_headers: dict):
    response = await client.get("/api/v1/tasks", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "tasks" in data
    assert "total" in data
