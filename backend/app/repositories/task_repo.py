from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Job, Task
from app.schemas.task import TaskCreate


class TaskRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, data: TaskCreate, user_id: str) -> Task:
        import json

        task = Task(
            user_id=user_id,
            title=data.title,
            description=data.description,
            priority=data.priority,
            due_date=data.due_date,
            recurring_cron=data.recurring_cron,
            tags_json=json.dumps(data.tags) if data.tags else None,
        )
        self.session.add(task)
        await self.session.flush()
        return task

    async def get(self, task_id: str, user_id: str) -> Task | None:
        result = await self.session.execute(
            select(Task).where(Task.id == task_id, Task.user_id == user_id),
        )
        return result.scalar_one_or_none()

    async def list_all(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
    ) -> tuple[list[Task], int]:
        query = select(Task).where(Task.user_id == user_id)
        if status:
            query = query.where(Task.status == status)

        count_result = await self.session.execute(
            select(func.count()).select_from(query.subquery()),
        )
        total = count_result.scalar_one()

        offset = (page - 1) * page_size
        result = await self.session.execute(
            query.order_by(Task.priority.desc(), Task.created_at.desc())
            .offset(offset)
            .limit(page_size),
        )
        return list(result.scalars().all()), total

    async def update(self, task_id: str, data: dict, user_id: str) -> Task | None:
        task = await self.get(task_id, user_id)
        if not task:
            return None
        for key, value in data.items():
            if value is not None:
                setattr(task, key, value)
        task.updated_at = datetime.now(UTC)
        await self.session.flush()
        return task

    async def complete(self, task_id: str, user_id: str) -> Task | None:
        task = await self.get(task_id, user_id)
        if not task:
            return None
        task.status = "completed"
        task.completed_at = datetime.now(UTC)
        task.updated_at = datetime.now(UTC)
        await self.session.flush()
        return task

    async def delete(self, task_id: str, user_id: str) -> bool:
        task = await self.get(task_id, user_id)
        if not task:
            return False
        await self.session.delete(task)
        await self.session.flush()
        return True

    async def get_overdue(self, user_id: str) -> list[Task]:
        now = datetime.now(UTC)
        result = await self.session.execute(
            select(Task).where(
                Task.user_id == user_id,
                Task.due_date < now,
                Task.status.in_(["pending", "in_progress"]),
            ),
        )
        return list(result.scalars().all())

    async def get_recurring(self, user_id: str) -> list[Task]:
        result = await self.session.execute(
            select(Task).where(
                Task.user_id == user_id,
                Task.recurring_cron.isnot(None),
                Task.status == "completed",
            ),
        )
        return list(result.scalars().all())


class JobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        name: str,
        job_type: str,
        payload: str | None = None,
        scheduled_at: datetime | None = None,
        max_attempts: int = 3,
    ) -> Job:
        job = Job(
            name=name,
            job_type=job_type,
            payload=payload,
            scheduled_at=scheduled_at,
            max_attempts=max_attempts,
        )
        self.session.add(job)
        await self.session.flush()
        return job

    async def get(self, job_id: str) -> Job | None:
        result = await self.session.execute(select(Job).where(Job.id == job_id))
        return result.scalar_one_or_none()

    async def get_pending(self) -> list[Job]:
        now = datetime.now(UTC)
        result = await self.session.execute(
            select(Job)
            .where(
                Job.status == "pending",
                (Job.scheduled_at.is_(None)) | (Job.scheduled_at <= now),
            )
            .order_by(Job.created_at.asc())
            .limit(10),
        )
        return list(result.scalars().all())

    async def update_status(
        self,
        job_id: str,
        status: str,
        result_text: str | None = None,
        error: str | None = None,
    ) -> Job | None:
        job = await self.get(job_id)
        if not job:
            return None
        job.status = status
        now = datetime.now(UTC)
        if status == "running":
            job.started_at = now
            job.attempts += 1
        elif status == "completed":
            job.completed_at = now
            job.result = result_text
        elif status == "failed":
            job.error_message = error
        job.updated_at = now
        await self.session.flush()
        return job

    async def list_all(self, page: int = 1, page_size: int = 20) -> tuple[list[Job], int]:
        count_result = await self.session.execute(select(func.count(Job.id)))
        total = count_result.scalar_one()
        offset = (page - 1) * page_size
        result = await self.session.execute(
            select(Job).order_by(Job.created_at.desc()).offset(offset).limit(page_size),
        )
        return list(result.scalars().all()), total

    async def cleanup_old(self, days: int = 30) -> int:
        cutoff = datetime.now(UTC)
        from datetime import timedelta

        cutoff = cutoff - timedelta(days=days)
        result = await self.session.execute(
            select(Job).where(
                Job.status.in_(["completed", "failed", "cancelled"]),
                Job.updated_at < cutoff,
            ),
        )
        jobs = list(result.scalars().all())
        for job in jobs:
            await self.session.delete(job)
        await self.session.flush()
        return len(jobs)
