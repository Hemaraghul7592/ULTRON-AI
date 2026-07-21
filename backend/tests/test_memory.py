from __future__ import annotations

import pytest

from app.memory.service import MemoryService
from app.repositories.memory_repo import MemoryRepository
from app.schemas.memory import MemoryCreate, MemoryUpdate


class TestMemoryRepository:
    @pytest.mark.asyncio
    async def test_create_and_get(self):
        from app.core.database import get_session

        session_factory = get_session()
        async with session_factory() as session:
            repo = MemoryRepository(session)
            data = MemoryCreate(content="Test memory", category="general", tags=["test"])
            memory = await repo.create(data, user_id="user-1")
            assert memory.id is not None
            assert memory.content == "Test memory"
            assert memory.category == "general"
            assert len(memory.tags) == 1
            assert memory.tags[0].name == "test"

            retrieved = await repo.get(memory.id, user_id="user-1")
            assert retrieved is not None
            assert retrieved.id == memory.id

    @pytest.mark.asyncio
    async def test_get_nonexistent(self):
        from app.core.database import get_session

        session_factory = get_session()
        async with session_factory() as session:
            repo = MemoryRepository(session)
            result = await repo.get("nonexistent", user_id="user-1")
            assert result is None

    @pytest.mark.asyncio
    async def test_list_all(self):
        from app.core.database import get_session

        session_factory = get_session()
        async with session_factory() as session:
            repo = MemoryRepository(session)
            for i in range(5):
                await repo.create(
                    MemoryCreate(content=f"Memory {i}", category="general"), user_id="user-1"
                )

            memories, total = await repo.list_all(user_id="user-1")
            assert total == 5
            assert len(memories) == 5

    @pytest.mark.asyncio
    async def test_list_all_filter_by_category(self):
        from app.core.database import get_session

        session_factory = get_session()
        async with session_factory() as session:
            repo = MemoryRepository(session)
            await repo.create(MemoryCreate(content="General", category="general"), user_id="user-1")
            await repo.create(
                MemoryCreate(content="Profile", category="user_profile"), user_id="user-1"
            )

            general_mems, g_total = await repo.list_all(user_id="user-1", category="general")
            assert g_total == 1
            assert general_mems[0].content == "General"

            profile_mems, p_total = await repo.list_all(user_id="user-1", category="user_profile")
            assert p_total == 1
            assert profile_mems[0].content == "Profile"

    @pytest.mark.asyncio
    async def test_list_all_excludes_archived(self):
        from app.core.database import get_session

        session_factory = get_session()
        async with session_factory() as session:
            repo = MemoryRepository(session)
            m1 = await repo.create(
                MemoryCreate(content="Active", category="general"), user_id="user-1"
            )
            m2 = await repo.create(
                MemoryCreate(content="Archived", category="general"), user_id="user-1"
            )
            m2.is_archived = True
            await session.flush()

            memories, total = await repo.list_all(user_id="user-1")
            assert total == 1
            assert memories[0].id == m1.id

    @pytest.mark.asyncio
    async def test_list_all_includes_archived_with_flag(self):
        from app.core.database import get_session

        session_factory = get_session()
        async with session_factory() as session:
            repo = MemoryRepository(session)
            await repo.create(MemoryCreate(content="Active", category="general"), user_id="user-1")
            m2 = await repo.create(
                MemoryCreate(content="Archived", category="general"), user_id="user-1"
            )
            m2.is_archived = True
            await session.flush()

            memories, total = await repo.list_all(user_id="user-1", include_archived=True)
            assert total == 2

    @pytest.mark.asyncio
    async def test_update(self):
        from app.core.database import get_session

        session_factory = get_session()
        async with session_factory() as session:
            repo = MemoryRepository(session)
            memory = await repo.create(
                MemoryCreate(content="Original", category="general"), user_id="user-1"
            )
            updated = await repo.update(memory.id, {"content": "Updated"}, user_id="user-1")
            assert updated is not None
            assert updated.content == "Updated"

    @pytest.mark.asyncio
    async def test_update_tags(self):
        from app.core.database import get_session

        session_factory = get_session()
        async with session_factory() as session:
            repo = MemoryRepository(session)
            memory = await repo.create(
                MemoryCreate(content="Tag test", tags=["a"]), user_id="user-1"
            )
            await repo.update(memory.id, {"tags": ["b", "c"]}, user_id="user-1")
            # Refresh to get updated tags
            await session.refresh(memory, attribute_names=["tags"])
            tag_names = [t.name for t in memory.tags]
            assert "b" in tag_names
            assert "c" in tag_names
            assert "a" not in tag_names

    @pytest.mark.asyncio
    async def test_update_wrong_user(self):
        from app.core.database import get_session

        session_factory = get_session()
        async with session_factory() as session:
            repo = MemoryRepository(session)
            memory = await repo.create(MemoryCreate(content="Original"), user_id="user-1")
            result = await repo.update(memory.id, {"content": "Hack"}, user_id="user-2")
            assert result is None

    @pytest.mark.asyncio
    async def test_delete(self):
        from app.core.database import get_session

        session_factory = get_session()
        async with session_factory() as session:
            repo = MemoryRepository(session)
            memory = await repo.create(MemoryCreate(content="To delete"), user_id="user-1")
            deleted = await repo.delete(memory.id, user_id="user-1")
            assert deleted is True
            retrieved = await repo.get(memory.id, user_id="user-1")
            assert retrieved is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self):
        from app.core.database import get_session

        session_factory = get_session()
        async with session_factory() as session:
            repo = MemoryRepository(session)
            result = await repo.delete("nonexistent", user_id="user-1")
            assert result is False

    @pytest.mark.asyncio
    async def test_search_by_content(self):
        from app.core.database import get_session

        session_factory = get_session()
        async with session_factory() as session:
            repo = MemoryRepository(session)
            await repo.create(MemoryCreate(content="The quick brown fox"), user_id="user-1")
            await repo.create(MemoryCreate(content="Jumped over the lazy dog"), user_id="user-1")
            await repo.create(MemoryCreate(content="Something else"), user_id="user-1")

            results = await repo.search_by_content("fox", user_id="user-1")
            assert len(results) == 1
            assert "fox" in results[0].content

    @pytest.mark.asyncio
    async def test_search_by_content_with_category(self):
        from app.core.database import get_session

        session_factory = get_session()
        async with session_factory() as session:
            repo = MemoryRepository(session)
            await repo.create(
                MemoryCreate(content="Python rocks", category="general"), user_id="user-1"
            )
            await repo.create(
                MemoryCreate(content="Python for ML", category="project"), user_id="user-1"
            )

            results = await repo.search_by_content("Python", user_id="user-1", category="project")
            assert len(results) == 1
            assert results[0].category == "project"

    @pytest.mark.asyncio
    async def test_get_by_category(self):
        from app.core.database import get_session

        session_factory = get_session()
        async with session_factory() as session:
            repo = MemoryRepository(session)
            await repo.create(
                MemoryCreate(content="Pref: dark mode", category="preference"), user_id="user-1"
            )
            await repo.create(
                MemoryCreate(content="Pref: long responses", category="preference"),
                user_id="user-1",
            )
            await repo.create(
                MemoryCreate(content="General note", category="general"), user_id="user-1"
            )

            results = await repo.get_by_category("preference", user_id="user-1")
            assert len(results) == 2

    @pytest.mark.asyncio
    async def test_user_isolation(self):
        from app.core.database import get_session

        session_factory = get_session()
        async with session_factory() as session:
            repo = MemoryRepository(session)
            await repo.create(MemoryCreate(content="User 1 memory"), user_id="user-1")
            await repo.create(MemoryCreate(content="User 2 memory"), user_id="user-2")

            u1_mems, u1_total = await repo.list_all(user_id="user-1")
            assert u1_total == 1

            u2_mems, u2_total = await repo.list_all(user_id="user-2")
            assert u2_total == 1


class TestMemoryService:
    @pytest.mark.asyncio
    async def test_create_memory(self):
        from app.core.database import get_session

        session_factory = get_session()
        async with session_factory() as session:
            service = MemoryService(session)
            result = await service.create_memory(
                MemoryCreate(content="Hello", category="general"),
                user_id="user-1",
            )
            assert result.id is not None
            assert result.content == "Hello"
            assert result.category == "general"

    @pytest.mark.asyncio
    async def test_create_with_category(self):
        from app.core.database import get_session

        session_factory = get_session()
        async with session_factory() as session:
            service = MemoryService(session)
            profile = await service.create_memory(
                MemoryCreate(content='{"name": "Alice"}', category="user_profile"),
                user_id="user-1",
            )
            assert profile.category == "user_profile"

            pref = await service.create_memory(
                MemoryCreate(content='{"style": "concise"}', category="preference"),
                user_id="user-1",
            )
            assert pref.category == "preference"

            proj = await service.create_memory(
                MemoryCreate(content="Build the AI engine", category="project"),
                user_id="user-1",
            )
            assert proj.category == "project"

            conv = await service.create_memory(
                MemoryCreate(content="Discussed plans for Q3", category="conversation"),
                user_id="user-1",
            )
            assert conv.category == "conversation"

    @pytest.mark.asyncio
    async def test_get_memory(self):
        from app.core.database import get_session

        session_factory = get_session()
        async with session_factory() as session:
            service = MemoryService(session)
            created = await service.create_memory(
                MemoryCreate(content="Get me"),
                user_id="user-1",
            )
            retrieved = await service.get_memory(created.id, user_id="user-1")
            assert retrieved is not None
            assert retrieved.content == "Get me"

    @pytest.mark.asyncio
    async def test_get_memory_not_found(self):
        from app.core.database import get_session

        session_factory = get_session()
        async with session_factory() as session:
            service = MemoryService(session)
            result = await service.get_memory("nonexistent", user_id="user-1")
            assert result is None

    @pytest.mark.asyncio
    async def test_update_memory(self):
        from app.core.database import get_session

        session_factory = get_session()
        async with session_factory() as session:
            service = MemoryService(session)
            created = await service.create_memory(
                MemoryCreate(content="Original"),
                user_id="user-1",
            )
            updated = await service.update_memory(
                created.id,
                MemoryUpdate(content="Updated"),
                user_id="user-1",
            )
            assert updated is not None
            assert updated.content == "Updated"

    @pytest.mark.asyncio
    async def test_update_not_found(self):
        from app.core.database import get_session

        session_factory = get_session()
        async with session_factory() as session:
            service = MemoryService(session)
            result = await service.update_memory(
                "nonexistent",
                MemoryUpdate(content="x"),
                user_id="user-1",
            )
            assert result is None

    @pytest.mark.asyncio
    async def test_delete_memory(self):
        from app.core.database import get_session

        session_factory = get_session()
        async with session_factory() as session:
            service = MemoryService(session)
            created = await service.create_memory(
                MemoryCreate(content="Delete me"),
                user_id="user-1",
            )
            deleted = await service.delete_memory(created.id, user_id="user-1")
            assert deleted is True
            retrieved = await service.get_memory(created.id, user_id="user-1")
            assert retrieved is None

    @pytest.mark.asyncio
    async def test_list_memories(self):
        from app.core.database import get_session

        session_factory = get_session()
        async with session_factory() as session:
            service = MemoryService(session)
            for i in range(5):
                await service.create_memory(
                    MemoryCreate(content=f"Item {i}", category="general"),
                    user_id="user-1",
                )
            result = await service.list_memories(user_id="user-1")
            assert result.total == 5
            assert len(result.memories) == 5

    @pytest.mark.asyncio
    async def test_list_filter_by_category(self):
        from app.core.database import get_session

        session_factory = get_session()
        async with session_factory() as session:
            service = MemoryService(session)
            await service.create_memory(
                MemoryCreate(content="General", category="general"), user_id="user-1"
            )
            await service.create_memory(
                MemoryCreate(content="Pref", category="preference"), user_id="user-1"
            )

            result = await service.list_memories(user_id="user-1", category="preference")
            assert result.total == 1
            assert result.memories[0].category == "preference"

    @pytest.mark.asyncio
    async def test_search_memories(self):
        from app.core.database import get_session

        session_factory = get_session()
        async with session_factory() as session:
            service = MemoryService(session)
            await service.create_memory(MemoryCreate(content="Python is great"), user_id="user-1")
            await service.create_memory(MemoryCreate(content="I like Java"), user_id="user-1")

            results = await service.search_memories("Python", user_id="user-1")
            assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_get_profile_memory(self):
        from app.core.database import get_session

        session_factory = get_session()
        async with session_factory() as session:
            service = MemoryService(session)
            await service.create_memory(
                MemoryCreate(content='{"name":"Alice"}', category="user_profile"),
                user_id="user-1",
            )
            profile = await service.get_profile_memory(user_id="user-1")
            assert profile is not None
            assert profile.category == "user_profile"

    @pytest.mark.asyncio
    async def test_get_preferences(self):
        from app.core.database import get_session

        session_factory = get_session()
        async with session_factory() as session:
            service = MemoryService(session)
            await service.create_memory(
                MemoryCreate(content="Dark mode", category="preference"),
                user_id="user-1",
            )
            await service.create_memory(
                MemoryCreate(content="Short answers", category="preference"),
                user_id="user-1",
            )
            prefs = await service.get_preferences(user_id="user-1")
            assert len(prefs) == 2

    @pytest.mark.asyncio
    async def test_get_project_memories(self):
        from app.core.database import get_session

        session_factory = get_session()
        async with session_factory() as session:
            service = MemoryService(session)
            await service.create_memory(
                MemoryCreate(content="Project Alpha", category="project"),
                user_id="user-1",
            )
            projects = await service.get_project_memories(user_id="user-1")
            assert len(projects) == 1
            assert projects[0].category == "project"

    @pytest.mark.asyncio
    async def test_archive_and_restore(self):
        from app.core.database import get_session

        session_factory = get_session()
        async with session_factory() as session:
            service = MemoryService(session)
            created = await service.create_memory(
                MemoryCreate(content="Archivable"), user_id="user-1"
            )

            archived = await service.archive_memory(created.id, user_id="user-1")
            assert archived is not None
            assert archived.is_archived is True

            result = await service.list_memories(user_id="user-1")
            assert result.total == 0

            restored = await service.restore_memory(created.id, user_id="user-1")
            assert restored is not None
            assert restored.is_archived is False

            result = await service.list_memories(user_id="user-1")
            assert result.total == 1

    @pytest.mark.asyncio
    async def test_archive_nonexistent(self):
        from app.core.database import get_session

        session_factory = get_session()
        async with session_factory() as session:
            service = MemoryService(session)
            result = await service.archive_memory("nonexistent", user_id="user-1")
            assert result is None

    @pytest.mark.asyncio
    async def test_get_context_for_query(self):
        from app.core.database import get_session

        session_factory = get_session()
        async with session_factory() as session:
            service = MemoryService(session)
            await service.create_memory(
                MemoryCreate(content="User likes Python programming"),
                user_id="user-1",
            )
            context = await service.get_context_for_query("Python", user_id="user-1")
            assert "Python" in context

    @pytest.mark.asyncio
    async def test_record_conversation_memory(self):
        from app.core.database import get_session

        session_factory = get_session()
        async with session_factory() as session:
            service = MemoryService(session)
            result = await service.record_conversation_memory(
                "Discussed project timeline",
                user_id="user-1",
                importance=0.7,
            )
            assert result.category == "conversation"
            assert result.importance == 0.7

    @pytest.mark.asyncio
    async def test_get_stats(self):
        from app.core.database import get_session

        session_factory = get_session()
        async with session_factory() as session:
            service = MemoryService(session)
            await service.create_memory(
                MemoryCreate(content="A", category="general"), user_id="user-1"
            )
            await service.create_memory(
                MemoryCreate(content="B", category="project"), user_id="user-1"
            )
            await service.create_memory(
                MemoryCreate(content="C", category="project"), user_id="user-1"
            )

            created = await service.create_memory(MemoryCreate(content="D"), user_id="user-1")
            await service.archive_memory(created.id, user_id="user-1")

            stats = await service.get_stats(user_id="user-1")
            assert stats["total"] == 3
            assert stats["archived"] == 1
            assert stats["by_category"]["general"] == 1
            assert stats["by_category"]["project"] == 2


class TestMemoryAPI:
    """Integration tests via the API client."""

    @pytest.mark.asyncio
    async def test_create_memory_endpoint(self, client, auth_headers):
        response = await client.post(
            "/api/v1/memory",
            json={"content": "API test memory", "category": "general"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["content"] == "API test memory"
        assert data["category"] == "general"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_list_memories_endpoint(self, client, auth_headers):
        # Create a memory first
        await client.post(
            "/api/v1/memory",
            json={"content": "List test", "category": "general"},
            headers=auth_headers,
        )
        response = await client.get("/api/v1/memory", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert len(data["memories"]) >= 1

    @pytest.mark.asyncio
    async def test_list_filter_by_category(self, client, auth_headers):
        await client.post(
            "/api/v1/memory",
            json={"content": "My profile", "category": "user_profile"},
            headers=auth_headers,
        )
        response = await client.get(
            "/api/v1/memory?category=user_profile",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert data["memories"][0]["category"] == "user_profile"

    @pytest.mark.asyncio
    async def test_get_memory_endpoint(self, client, auth_headers):
        create_resp = await client.post(
            "/api/v1/memory",
            json={"content": "Get me", "category": "general"},
            headers=auth_headers,
        )
        memory_id = create_resp.json()["id"]

        response = await client.get(f"/api/v1/memory/{memory_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["content"] == "Get me"

    @pytest.mark.asyncio
    async def test_get_memory_not_found(self, client, auth_headers):
        response = await client.get("/api/v1/memory/nonexistent-id", headers=auth_headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_memory_endpoint(self, client, auth_headers):
        create_resp = await client.post(
            "/api/v1/memory",
            json={"content": "Original", "category": "general"},
            headers=auth_headers,
        )
        memory_id = create_resp.json()["id"]

        response = await client.patch(
            f"/api/v1/memory/{memory_id}",
            json={"content": "Updated"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["content"] == "Updated"

    @pytest.mark.asyncio
    async def test_delete_memory_endpoint(self, client, auth_headers):
        create_resp = await client.post(
            "/api/v1/memory",
            json={"content": "Delete me"},
            headers=auth_headers,
        )
        memory_id = create_resp.json()["id"]

        response = await client.delete(f"/api/v1/memory/{memory_id}", headers=auth_headers)
        assert response.status_code == 204

        # Verify it's gone
        get_resp = await client.get(f"/api/v1/memory/{memory_id}", headers=auth_headers)
        assert get_resp.status_code == 404

    @pytest.mark.asyncio
    async def test_archive_endpoint(self, client, auth_headers):
        create_resp = await client.post(
            "/api/v1/memory",
            json={"content": "Archive me", "category": "general"},
            headers=auth_headers,
        )
        memory_id = create_resp.json()["id"]

        response = await client.patch(f"/api/v1/memory/{memory_id}/archive", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["is_archived"] is True

    @pytest.mark.asyncio
    async def test_restore_endpoint(self, client, auth_headers):
        create_resp = await client.post(
            "/api/v1/memory",
            json={"content": "Restore me"},
            headers=auth_headers,
        )
        memory_id = create_resp.json()["id"]

        await client.patch(f"/api/v1/memory/{memory_id}/archive", headers=auth_headers)
        response = await client.patch(f"/api/v1/memory/{memory_id}/restore", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["is_archived"] is False

    @pytest.mark.asyncio
    async def test_promote_endpoint(self, client, auth_headers):
        create_resp = await client.post(
            "/api/v1/memory",
            json={"content": "Promote me", "memory_type": "short_term", "importance": 0.8},
            headers=auth_headers,
        )
        memory_id = create_resp.json()["id"]

        response = await client.patch(f"/api/v1/memory/{memory_id}/promote", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["memory_type"] == "long_term"

    @pytest.mark.asyncio
    async def test_search_memories_endpoint(self, client, auth_headers):
        await client.post(
            "/api/v1/memory",
            json={"content": "Search for this keyword"},
            headers=auth_headers,
        )
        response = await client.post(
            "/api/v1/memory/search",
            json={"query": "keyword"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["memories"]) >= 1

    @pytest.mark.asyncio
    async def test_stats_endpoint(self, client, auth_headers):
        response = await client.get("/api/v1/memory/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "by_category" in data
        assert "archived" in data

    @pytest.mark.asyncio
    async def test_profile_memory_endpoint(self, client, auth_headers):
        await client.post(
            "/api/v1/memory",
            json={"content": '{"name":"Bob"}', "category": "user_profile"},
            headers=auth_headers,
        )
        response = await client.get("/api/v1/memory/profile", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data is not None
        assert data["category"] == "user_profile"

    @pytest.mark.asyncio
    async def test_preferences_endpoint(self, client, auth_headers):
        await client.post(
            "/api/v1/memory",
            json={"content": "Dark mode", "category": "preference"},
            headers=auth_headers,
        )
        response = await client.get("/api/v1/memory/preferences", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_projects_endpoint(self, client, auth_headers):
        await client.post(
            "/api/v1/memory",
            json={"content": "Project X", "category": "project"},
            headers=auth_headers,
        )
        response = await client.get("/api/v1/memory/projects", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_unauthorized_access(self, client):
        response = await client.get("/api/v1/memory")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_user_isolation_api(self, client):
        # Register two users
        r1 = await client.post(
            "/api/v1/auth/register", json={"username": "user_one", "password": "Test1234!"}
        )
        token1 = r1.json()["access_token"]
        headers1 = {"Authorization": f"Bearer {token1}"}

        r2 = await client.post(
            "/api/v1/auth/register", json={"username": "user_two", "password": "Test1234!"}
        )
        token2 = r2.json()["access_token"]
        headers2 = {"Authorization": f"Bearer {token2}"}

        await client.post("/api/v1/memory", json={"content": "User 1 data"}, headers=headers1)
        await client.post("/api/v1/memory", json={"content": "User 2 data"}, headers=headers2)

        resp1 = await client.get("/api/v1/memory", headers=headers1)
        resp2 = await client.get("/api/v1/memory", headers=headers2)

        assert resp1.json()["total"] == 1
        assert resp2.json()["total"] == 1
