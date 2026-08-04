from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: TC002
from sqlalchemy.orm import selectinload

from app.models.memory import Memory, Tag, memory_tags
from app.repositories.utils import escape_like
from app.schemas.memory import MemoryCreate  # noqa: TC001


class MemoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        data: MemoryCreate,
        user_id: str,
        embedding: str | None = None,
    ) -> Memory:
        memory = Memory(
            user_id=user_id,
            content=data.content,
            memory_type=data.memory_type,
            category=data.category,
            importance=data.importance,
            source=data.source,
            context=data.context,
            embedding_vector=embedding,
        )
        self.session.add(memory)
        await self.session.flush()

        if data.tags:
            for tag_name in data.tags:
                tag = await self._get_or_create_tag(tag_name)
                # Insert into association table directly to avoid lazy-load
                await self.session.execute(
                    memory_tags.insert().values(memory_id=memory.id, tag_id=tag.id),
                )

        # Re-query to get memory with tags loaded eagerly
        result = await self.session.execute(
            select(Memory).options(selectinload(Memory.tags)).where(Memory.id == memory.id),
        )
        return result.scalar_one()

    async def get(self, memory_id: str, user_id: str) -> Memory | None:
        result = await self.session.execute(
            select(Memory)
            .options(selectinload(Memory.tags))
            .where(Memory.id == memory_id, Memory.user_id == user_id),
        )
        return result.scalar_one_or_none()

    async def list_all(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
        memory_type: str | None = None,
        category: str | None = None,
        min_importance: float = 0.0,
        include_archived: bool = False,
    ) -> tuple[list[Memory], int]:
        conditions = [Memory.user_id == user_id, Memory.importance >= min_importance]
        if memory_type:
            conditions.append(Memory.memory_type == memory_type)
        if category:
            conditions.append(Memory.category == category)
        if not include_archived:
            conditions.append(Memory.is_archived == False)  # noqa: E712

        query = select(Memory).where(*conditions)

        count_result = await self.session.execute(
            select(func.count()).select_from(query.subquery()),
        )
        total = count_result.scalar_one()

        offset = (page - 1) * page_size
        result = await self.session.execute(
            query.options(selectinload(Memory.tags))
            .order_by(Memory.importance.desc())
            .offset(offset)
            .limit(page_size),
        )
        return list(result.scalars().all()), total

    async def update(self, memory_id: str, data: dict, user_id: str) -> Memory | None:
        memory = await self.get(memory_id, user_id)
        if not memory:
            return None
        for key, value in data.items():
            if key == "tags" and isinstance(value, list):
                # Delete existing associations and re-insert
                await self.session.execute(
                    memory_tags.delete().where(memory_tags.c.memory_id == memory.id),
                )
                for tag_name in value:
                    tag = await self._get_or_create_tag(tag_name)
                    await self.session.execute(
                        memory_tags.insert().values(memory_id=memory.id, tag_id=tag.id),
                    )
            elif value is not None:
                setattr(memory, key, value)
        memory.updated_at = datetime.now(UTC)
        await self.session.flush()
        # Re-query to get fresh state with tags
        result = await self.session.execute(
            select(Memory).options(selectinload(Memory.tags)).where(Memory.id == memory.id),
        )
        return result.scalar_one()

    async def delete(self, memory_id: str, user_id: str) -> bool:
        memory = await self.get(memory_id, user_id)
        if not memory:
            return False
        await self.session.delete(memory)
        await self.session.flush()
        return True

    async def search_by_content(
        self,
        query: str,
        user_id: str,
        limit: int = 10,
        memory_type: str | None = None,
        category: str | None = None,
        min_importance: float = 0.0,
    ) -> list[Memory]:
        conditions = [
            Memory.user_id == user_id,
            Memory.content.ilike(f"%{escape_like(query)}%"),
            Memory.importance >= min_importance,
        ]
        if memory_type:
            conditions.append(Memory.memory_type == memory_type)
        if category:
            conditions.append(Memory.category == category)

        q = (
            select(Memory)
            .options(selectinload(Memory.tags))
            .where(*conditions)
            .order_by(Memory.importance.desc())
            .limit(limit)
        )
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def get_by_type(self, memory_type: str, user_id: str, limit: int = 50) -> list[Memory]:
        result = await self.session.execute(
            select(Memory)
            .where(Memory.memory_type == memory_type, Memory.user_id == user_id)
            .order_by(Memory.importance.desc())
            .limit(limit),
        )
        return list(result.scalars().all())

    async def get_by_category(self, category: str, user_id: str, limit: int = 50) -> list[Memory]:
        result = await self.session.execute(
            select(Memory)
            .options(selectinload(Memory.tags))
            .where(
                Memory.category == category,
                Memory.user_id == user_id,
                Memory.is_archived == False,  # noqa: E712
            )
            .order_by(Memory.importance.desc())
            .limit(limit),
        )
        return list(result.scalars().all())

    async def increment_access(self, memory_id: str, user_id: str) -> None:
        memory = await self.get(memory_id, user_id)
        if memory:
            memory.access_count += 1
            memory.last_accessed = datetime.now(UTC)
            await self.session.flush()

    async def promote_to_long_term(self, user_id: str, threshold: float = 0.7) -> int:
        result = await self.session.execute(
            select(Memory).where(
                Memory.user_id == user_id,
                Memory.memory_type == "short_term",
                Memory.importance >= threshold,
            ),
        )
        memories = list(result.scalars().all())
        for memory in memories:
            memory.memory_type = "long_term"
            memory.updated_at = datetime.now(UTC)
        await self.session.flush()
        return len(memories)

    async def _get_or_create_tag(self, name: str) -> Tag:
        result = await self.session.execute(select(Tag).where(Tag.name == name))
        tag = result.scalar_one_or_none()
        if not tag:
            tag = Tag(name=name)
            self.session.add(tag)
            await self.session.flush()
        return tag
