import os

os.environ["SECRET_KEY"] = "d41d8cd98f00b204e9800998ecf8427e"
os.environ["ENCRYPTION_KEY"] = (
    "dGVzdC1rZXktdGhhdC1pcy1hdC1sZWFzdC0zMi1ieXRlcy1sb25nLWZvci1mZXJuZXQh"
)
os.environ["RATE_LIMIT_PER_MINUTE"] = "1000"
os.environ["RATE_LIMIT_AUTH_PER_MINUTE"] = "1000"

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import Base, init_db
from app.main import app


@pytest.fixture(autouse=True)
async def setup_database():
    await init_db()
    from app.core.database import engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    from app.core.database import close_db

    await close_db()
    if hasattr(app.state, "uaes_runtime"):
        delattr(app.state, "uaes_runtime")


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def auth_headers(client: AsyncClient):
    r = await client.post(
        "/api/v1/auth/register",
        json={"username": "testuser", "password": "TestPass123!"},
    )
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
