from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.repositories.memory_repo import MemoryRepository
from app.schemas.memory import (
    MemoryCreate,
    MemoryListResponse,
    MemoryResponse,
    MemoryUpdate,
    TagResponse,
)

logger = get_logger(__name__)


class MemoryService:
    """Single entry point for all memory operations.

    All modules (AI, Chat, future Plugins, Search, Voice, Agents)
    must use this service to interact with memory storage.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.repo = MemoryRepository(session)

    # ── CRUD ──────────────────────────────────────────────────

    async def create_memory(self, data: MemoryCreate, user_id: str) -> MemoryResponse:
        memory = await self.repo.create(data, user_id=user_id)
        return self._to_response(memory)

    async def get_memory(self, memory_id: str, user_id: str) -> MemoryResponse | None:
        memory = await self.repo.get(memory_id, user_id)
        if memory is None:
            return None
        return self._to_response(memory)

    async def update_memory(
        self, memory_id: str, data: MemoryUpdate, user_id: str
    ) -> MemoryResponse | None:
        update_dict = data.model_dump(exclude_unset=True)
        if not update_dict:
            existing = await self.repo.get(memory_id, user_id)
            return self._to_response(existing) if existing else None
        memory = await self.repo.update(memory_id, update_dict, user_id)
        if memory is None:
            return None
        return self._to_response(memory)

    async def delete_memory(self, memory_id: str, user_id: str) -> bool:
        return await self.repo.delete(memory_id, user_id)

    # ── List / Search ─────────────────────────────────────────

    async def list_memories(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
        memory_type: str | None = None,
        category: str | None = None,
        min_importance: float = 0.0,
        include_archived: bool = False,
    ) -> MemoryListResponse:
        memories, total = await self.repo.list_all(
            user_id=user_id,
            page=page,
            page_size=page_size,
            memory_type=memory_type,
            category=category,
            min_importance=min_importance,
            include_archived=include_archived,
        )
        return MemoryListResponse(
            memories=[self._to_response(m) for m in memories],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def search_memories(
        self,
        query: str,
        user_id: str,
        limit: int = 10,
        memory_type: str | None = None,
        category: str | None = None,
        min_importance: float = 0.0,
    ) -> list[dict[str, Any]]:
        results = await self.repo.search_by_content(
            query=query,
            user_id=user_id,
            limit=limit,
            memory_type=memory_type,
            category=category,
            min_importance=min_importance,
        )
        return [{"memory": self._to_response(m), "score": 1.0} for m in results]

    # ── Category convenience ──────────────────────────────────

    async def get_by_category(
        self, category: str, user_id: str, limit: int = 50
    ) -> list[MemoryResponse]:
        memories = await self.repo.get_by_category(category, user_id=user_id, limit=limit)
        return [self._to_response(m) for m in memories]

    async def get_profile_memory(self, user_id: str) -> MemoryResponse | None:
        memories = await self.repo.get_by_category("user_profile", user_id=user_id, limit=1)
        return self._to_response(memories[0]) if memories else None

    async def get_preferences(self, user_id: str) -> list[MemoryResponse]:
        return await self.get_by_category("preference", user_id=user_id)

    async def get_project_memories(self, user_id: str) -> list[MemoryResponse]:
        return await self.get_by_category("project", user_id=user_id)

    async def record_conversation_memory(
        self,
        summary: str,
        user_id: str,
        importance: float = 0.5,
        tags: list[str] | None = None,
    ) -> MemoryResponse:
        data = MemoryCreate(
            content=summary,
            memory_type="short_term",
            category="conversation",
            importance=importance,
            source="chat",
            tags=tags or ["conversation"],
        )
        return await self.create_memory(data, user_id)

    # ── Archive / Restore ─────────────────────────────────────

    async def archive_memory(self, memory_id: str, user_id: str) -> MemoryResponse | None:
        memory = await self.repo.get(memory_id, user_id)
        if memory is None:
            return None
        memory.is_archived = True
        await self.repo.session.flush()
        return self._to_response(memory)

    async def restore_memory(self, memory_id: str, user_id: str) -> MemoryResponse | None:
        memory = await self.repo.get(memory_id, user_id)
        if memory is None:
            return None
        memory.is_archived = False
        await self.repo.session.flush()
        return self._to_response(memory)

    # ── AI Integration ────────────────────────────────────────

    async def get_context_for_query(
        self,
        query: str,
        user_id: str,
        limit: int = 5,
        categories: list[str] | None = None,
    ) -> str:
        memories = await self.repo.search_by_content(
            query=query,
            user_id=user_id,
            limit=limit,
            category=None,
            min_importance=0.0,
        )
        if not memories:
            return ""
        if categories:
            memories = [m for m in memories if m.category in categories]
        lines = []
        for m in memories[:limit]:
            label = f"[{m.category}]" if m.category != "general" else ""
            lines.append(f"- {label} {m.content}")
        return "\n".join(lines)

    # ── Stats ─────────────────────────────────────────────────

    async def get_stats(self, user_id: str) -> dict[str, Any]:
        from sqlalchemy import func, select

        from app.models.memory import Memory

        session = self.repo.session
        results = await session.execute(
            select(Memory.category, func.count())
            .where(
                Memory.user_id == user_id,
                Memory.is_archived == False,  # noqa: E712
            )
            .group_by(Memory.category),
        )
        counts: dict[str, int] = {}
        total = 0
        for row in results:
            counts[row[0]] = row[1]
            total += row[1]

        archived_result = await session.execute(
            select(func.count()).where(
                Memory.user_id == user_id,
                Memory.is_archived == True,  # noqa: E712
            ),
        )
        archived_count = archived_result.scalar_one()

        return {
            "total": total,
            "archived": archived_count,
            "by_category": counts,
        }

    # ── Helpers ───────────────────────────────────────────────

    @staticmethod
    def _to_response(memory: Any) -> MemoryResponse:
        return MemoryResponse(
            id=memory.id,
            content=memory.content,
            summary=memory.summary,
            memory_type=memory.memory_type,
            category=memory.category,
            is_archived=memory.is_archived,
            importance=memory.importance,
            access_count=memory.access_count,
            source=memory.source,
            context=memory.context,
            tags=[TagResponse(id=t.id, name=t.name, created_at=t.created_at) for t in memory.tags],
            created_at=memory.created_at,
            updated_at=memory.updated_at,
            last_accessed=memory.last_accessed,
        )
