from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.v1.auth import verify_token
from app.core.database import get_session
from app.repositories.task_repo import TaskRepository
from app.schemas.task import TaskCreate, TaskListResponse, TaskResponse, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"], dependencies=[Depends(verify_token)])


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    user: dict = Depends(verify_token),
) -> TaskListResponse:
    user_id = user["user_id"]
    session_factory = get_session()
    async with session_factory() as session:
        repo = TaskRepository(session)
        tasks, total = await repo.list_all(
            user_id=user_id, page=page, page_size=page_size, status=status,
        )
        return TaskListResponse(
            tasks=[TaskResponse.model_validate(t) for t in tasks],
            total=total,
            page=page,
            page_size=page_size,
        )


@router.post("", response_model=TaskResponse, status_code=201)
async def create_task(data: TaskCreate, user: dict = Depends(verify_token)) -> TaskResponse:
    user_id = user["user_id"]
    session_factory = get_session()
    async with session_factory() as session:
        repo = TaskRepository(session)
        task = await repo.create(data, user_id=user_id)
        await session.commit()
        return TaskResponse.model_validate(task)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, user: dict = Depends(verify_token)) -> TaskResponse:
    user_id = user["user_id"]
    session_factory = get_session()
    async with session_factory() as session:
        repo = TaskRepository(session)
        task = await repo.get(task_id, user_id)
        if not task:
            from app.core.exceptions import NotFoundExceptionHTTP

            raise NotFoundExceptionHTTP("Task", task_id)
        return TaskResponse.model_validate(task)


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str, data: TaskUpdate, user: dict = Depends(verify_token),
) -> TaskResponse:
    user_id = user["user_id"]
    session_factory = get_session()
    async with session_factory() as session:
        repo = TaskRepository(session)
        task = await repo.update(task_id, data.model_dump(exclude_unset=True), user_id=user_id)
        if not task:
            from app.core.exceptions import NotFoundExceptionHTTP

            raise NotFoundExceptionHTTP("Task", task_id)
        await session.commit()
        return TaskResponse.model_validate(task)


@router.post("/{task_id}/complete", response_model=TaskResponse)
async def complete_task(task_id: str, user: dict = Depends(verify_token)) -> TaskResponse:
    user_id = user["user_id"]
    session_factory = get_session()
    async with session_factory() as session:
        repo = TaskRepository(session)
        task = await repo.complete(task_id, user_id=user_id)
        if not task:
            from app.core.exceptions import NotFoundExceptionHTTP

            raise NotFoundExceptionHTTP("Task", task_id)
        await session.commit()
        return TaskResponse.model_validate(task)


@router.delete("/{task_id}", status_code=204)
async def delete_task(task_id: str, user: dict = Depends(verify_token)) -> None:
    user_id = user["user_id"]
    session_factory = get_session()
    async with session_factory() as session:
        repo = TaskRepository(session)
        deleted = await repo.delete(task_id, user_id=user_id)
        if not deleted:
            from app.core.exceptions import NotFoundExceptionHTTP

            raise NotFoundExceptionHTTP("Task", task_id)
        await session.commit()
