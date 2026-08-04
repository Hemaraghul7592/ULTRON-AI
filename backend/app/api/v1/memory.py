from __future__ import annotations

from fastapi import APIRouter, Depends, Path, Query

from app.api.v1.auth import verify_token
from app.core.database import get_session
from app.memory.service import MemoryService
from app.schemas.memory import (
    MemoryCreate,
    MemoryListResponse,
    MemoryResponse,
    MemorySearchRequest,
    MemorySearchResponse,
    MemoryUpdate,
)

router = APIRouter(prefix="/memory", tags=["memory"], dependencies=[Depends(verify_token)])


def _get_service():
    session_factory = get_session()
    session = session_factory()
    return MemoryService(session), session


# ── List / Create (static paths before parameterized) ──────────


@router.get("", response_model=MemoryListResponse)
async def list_memories(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    memory_type: str | None = Query(
        default=None, pattern="^(short_term|long_term|episodic|semantic)$",
    ),
    category: str | None = Query(
        default=None, pattern="^(general|user_profile|preference|project|conversation)$",
    ),
    min_importance: float = Query(0.0, ge=0.0, le=1.0),
    include_archived: bool = Query(False),
    user: dict = Depends(verify_token),
) -> MemoryListResponse:
    user_id = user["user_id"]
    service, session = _get_service()
    async with session:
        return await service.list_memories(
            user_id=user_id,
            page=page,
            page_size=page_size,
            memory_type=memory_type,
            category=category,
            min_importance=min_importance,
            include_archived=include_archived,
        )


@router.post("", response_model=MemoryResponse, status_code=201)
async def create_memory(data: MemoryCreate, user: dict = Depends(verify_token)) -> MemoryResponse:
    user_id = user["user_id"]
    service, session = _get_service()
    async with session:
        result = await service.create_memory(data, user_id=user_id)
        await session.commit()
        return result


@router.post("/search", response_model=MemorySearchResponse)
async def search_memories(
    data: MemorySearchRequest, user: dict = Depends(verify_token),
) -> MemorySearchResponse:
    user_id = user["user_id"]
    service, session = _get_service()
    async with session:
        results = await service.search_memories(
            query=data.query,
            user_id=user_id,
            limit=data.limit,
            memory_type=data.memory_type,
            category=data.category,
            min_importance=data.min_importance,
        )
        return MemorySearchResponse(
            memories=[r["memory"] for r in results],
            scores=[r["score"] for r in results],
            query=data.query,
        )


@router.get("/stats")
async def memory_stats(user: dict = Depends(verify_token)) -> dict:
    user_id = user["user_id"]
    service, session = _get_service()
    async with session:
        return await service.get_stats(user_id=user_id)


# ── Category-specific convenience endpoints ──────────────────


@router.get("/profile", response_model=MemoryResponse | None)
async def get_profile_memory(user: dict = Depends(verify_token)) -> MemoryResponse | None:
    user_id = user["user_id"]
    service, session = _get_service()
    async with session:
        return await service.get_profile_memory(user_id)


@router.get("/preferences", response_model=list[MemoryResponse])
async def get_preferences(user: dict = Depends(verify_token)) -> list[MemoryResponse]:
    user_id = user["user_id"]
    service, session = _get_service()
    async with session:
        return await service.get_preferences(user_id)


@router.get("/projects", response_model=list[MemoryResponse])
async def get_project_memories(user: dict = Depends(verify_token)) -> list[MemoryResponse]:
    user_id = user["user_id"]
    service, session = _get_service()
    async with session:
        return await service.get_project_memories(user_id)


# ── Individual memory CRUD (parameterized paths last) ────────


@router.get("/{memory_id}", response_model=MemoryResponse)
async def get_memory(
    memory_id: str = Path(..., min_length=1, max_length=36), user: dict = Depends(verify_token),
) -> MemoryResponse:
    user_id = user["user_id"]
    service, session = _get_service()
    async with session:
        memory = await service.get_memory(memory_id, user_id)
        if memory is None:
            from app.core.exceptions import NotFoundExceptionHTTP

            raise NotFoundExceptionHTTP("Memory", memory_id)
        return memory


@router.patch("/{memory_id}", response_model=MemoryResponse)
async def update_memory(
    data: MemoryUpdate,
    memory_id: str = Path(..., min_length=1, max_length=36),
    user: dict = Depends(verify_token),
) -> MemoryResponse:
    user_id = user["user_id"]
    service, session = _get_service()
    async with session:
        memory = await service.update_memory(memory_id, data, user_id=user_id)
        if memory is None:
            from app.core.exceptions import NotFoundExceptionHTTP

            raise NotFoundExceptionHTTP("Memory", memory_id)
        await session.commit()
        return memory


@router.delete("/{memory_id}", status_code=204)
async def delete_memory(
    memory_id: str = Path(..., min_length=1, max_length=36), user: dict = Depends(verify_token),
) -> None:
    user_id = user["user_id"]
    service, session = _get_service()
    async with session:
        deleted = await service.delete_memory(memory_id, user_id=user_id)
        if not deleted:
            from app.core.exceptions import NotFoundExceptionHTTP

            raise NotFoundExceptionHTTP("Memory", memory_id)
        await session.commit()


@router.patch("/{memory_id}/archive", response_model=MemoryResponse)
async def archive_memory(memory_id: str, user: dict = Depends(verify_token)) -> MemoryResponse:
    user_id = user["user_id"]
    service, session = _get_service()
    async with session:
        memory = await service.archive_memory(memory_id, user_id)
        if memory is None:
            from app.core.exceptions import NotFoundExceptionHTTP

            raise NotFoundExceptionHTTP("Memory", memory_id)
        await session.commit()
        return memory


@router.patch("/{memory_id}/restore", response_model=MemoryResponse)
async def restore_memory(memory_id: str, user: dict = Depends(verify_token)) -> MemoryResponse:
    user_id = user["user_id"]
    service, session = _get_service()
    async with session:
        memory = await service.restore_memory(memory_id, user_id)
        if memory is None:
            from app.core.exceptions import NotFoundExceptionHTTP

            raise NotFoundExceptionHTTP("Memory", memory_id)
        await session.commit()
        return memory


@router.patch("/{memory_id}/promote")
async def promote_memory(memory_id: str, user: dict = Depends(verify_token)) -> dict:
    user_id = user["user_id"]
    service, session = _get_service()
    async with session:
        from app.schemas.memory import MemoryUpdate as MU

        memory = await service.update_memory(
            memory_id, MU(memory_type="long_term"), user_id=user_id,
        )
        if memory is None:
            from app.core.exceptions import NotFoundExceptionHTTP

            raise NotFoundExceptionHTTP("Memory", memory_id)
        await session.commit()
        return {"id": memory.id, "memory_type": memory.memory_type}
