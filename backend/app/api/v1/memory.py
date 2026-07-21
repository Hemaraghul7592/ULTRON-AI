from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import verify_token
from app.core.database import get_session
from app.memory.engine import MemoryEngine
from app.repositories.memory_repo import MemoryRepository
from app.schemas.memory import (
    MemoryCreate,
    MemoryListResponse,
    MemoryResponse,
    MemorySearchRequest,
    MemorySearchResponse,
    MemoryUpdate,
    TagResponse,
)

router = APIRouter(prefix="/memory", tags=["memory"], dependencies=[Depends(verify_token)])


@router.get("", response_model=MemoryListResponse)
async def list_memories(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    memory_type: str | None = None,
    min_importance: float = Query(0.0, ge=0.0, le=1.0),
    user: dict = Depends(verify_token),
) -> MemoryListResponse:
    user_id = user["user_id"]
    session_factory = get_session()
    async with session_factory() as session:
        repo = MemoryRepository(session)
        memories, total = await repo.list_all(
            user_id=user_id, page=page, page_size=page_size, memory_type=memory_type, min_importance=min_importance
        )
        return MemoryListResponse(
            memories=[
                MemoryResponse(
                    id=m.id,
                    content=m.content,
                    summary=m.summary,
                    memory_type=m.memory_type,
                    importance=m.importance,
                    access_count=m.access_count,
                    source=m.source,
                    context=m.context,
                    tags=[TagResponse(id=t.id, name=t.name, created_at=t.created_at) for t in m.tags],
                    created_at=m.created_at,
                    updated_at=m.updated_at,
                    last_accessed=m.last_accessed,
                )
                for m in memories
            ],
            total=total,
            page=page,
            page_size=page_size,
        )


@router.post("", response_model=MemoryResponse, status_code=201)
async def create_memory(data: MemoryCreate, user: dict = Depends(verify_token)) -> MemoryResponse:
    user_id = user["user_id"]
    session_factory = get_session()
    async with session_factory() as session:
        engine = MemoryEngine(session)
        await engine.initialize()
        memory = await engine.store(data, user_id=user_id)
        await session.commit()
        return MemoryResponse(
            id=memory.id,
            content=memory.content,
            summary=memory.summary,
            memory_type=memory.memory_type,
            importance=memory.importance,
            access_count=memory.access_count,
            source=memory.source,
            context=memory.context,
            tags=[TagResponse(id=t.id, name=t.name, created_at=t.created_at) for t in memory.tags],
            created_at=memory.created_at,
            updated_at=memory.updated_at,
            last_accessed=memory.last_accessed,
        )


@router.post("/search", response_model=MemorySearchResponse)
async def search_memories(data: MemorySearchRequest, user: dict = Depends(verify_token)) -> MemorySearchResponse:
    user_id = user["user_id"]
    session_factory = get_session()
    async with session_factory() as session:
        engine = MemoryEngine(session)
        await engine.initialize()
        results = await engine.search(
            query=data.query,
            user_id=user_id,
            limit=data.limit,
            memory_type=data.memory_type,
            min_importance=data.min_importance,
        )
        return MemorySearchResponse(
            memories=[
                MemoryResponse(
                    id=r["memory"].id,
                    content=r["memory"].content,
                    summary=r["memory"].summary,
                    memory_type=r["memory"].memory_type,
                    importance=r["memory"].importance,
                    access_count=r["memory"].access_count,
                    source=r["memory"].source,
                    context=r["memory"].context,
                    tags=[TagResponse(id=t.id, name=t.name, created_at=t.created_at) for t in r["memory"].tags],
                    created_at=r["memory"].created_at,
                    updated_at=r["memory"].updated_at,
                    last_accessed=r["memory"].last_accessed,
                )
                for r in results
            ],
            scores=[r["score"] for r in results],
            query=data.query,
        )


@router.get("/stats")
async def memory_stats(user: dict = Depends(verify_token)) -> dict:
    user_id = user["user_id"]
    session_factory = get_session()
    async with session_factory() as session:
        engine = MemoryEngine(session)
        await engine.initialize()
        return await engine.get_stats(user_id=user_id)


@router.patch("/{memory_id}/promote")
async def promote_memory(memory_id: str, user: dict = Depends(verify_token)) -> dict:
    user_id = user["user_id"]
    session_factory = get_session()
    async with session_factory() as session:
        repo = MemoryRepository(session)
        memory = await repo.update(memory_id, {"memory_type": "long_term"}, user_id=user_id)
        if not memory:
            from app.core.exceptions import NotFoundExceptionHTTP
            raise NotFoundExceptionHTTP("Memory", memory_id)
        await session.commit()
        return {"id": memory.id, "memory_type": memory.memory_type}