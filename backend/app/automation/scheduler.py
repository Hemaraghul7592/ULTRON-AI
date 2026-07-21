from __future__ import annotations

import asyncio
import time
from typing import Any, Callable, Coroutine

from app.core.logging import get_logger

logger = get_logger(__name__)


class ScheduledJob:
    def __init__(
        self,
        job_id: str,
        name: str,
        func: Callable[..., Coroutine[Any, Any, Any]],
        interval_seconds: float,
        args: tuple = (),
        kwargs: dict | None = None,
    ) -> None:
        self.job_id = job_id
        self.name = name
        self.func = func
        self.interval_seconds = interval_seconds
        self.args = args
        self.kwargs = kwargs or {}
        self.last_run: float = 0
        self.run_count: int = 0
        self.is_running: bool = False
        self.enabled: bool = True

    def should_run(self) -> bool:
        if not self.enabled or self.is_running:
            return False
        return (time.monotonic() - self.last_run) >= self.interval_seconds


class SchedulerService:
    def __init__(self) -> None:
        self._jobs: dict[str, ScheduledJob] = {}
        self._running = False
        self._task: asyncio.Task | None = None

    def add_job(
        self,
        job_id: str,
        name: str,
        func: Callable[..., Coroutine[Any, Any, Any]],
        interval_seconds: float,
        args: tuple = (),
        kwargs: dict | None = None,
    ) -> ScheduledJob:
        job = ScheduledJob(
            job_id=job_id,
            name=name,
            func=func,
            interval_seconds=interval_seconds,
            args=args,
            kwargs=kwargs,
        )
        self._jobs[job_id] = job
        logger.info("job_scheduled", job_id=job_id, name=name, interval=interval_seconds)
        return job

    def remove_job(self, job_id: str) -> bool:
        if job_id in self._jobs:
            del self._jobs[job_id]
            logger.info("job_removed", job_id=job_id)
            return True
        return False

    def pause_job(self, job_id: str) -> bool:
        job = self._jobs.get(job_id)
        if job:
            job.enabled = False
            return True
        return False

    def resume_job(self, job_id: str) -> bool:
        job = self._jobs.get(job_id)
        if job:
            job.enabled = True
            return True
        return False

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("scheduler_started", job_count=len(self._jobs))

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("scheduler_stopped")

    async def _run_loop(self) -> None:
        while self._running:
            for job in self._jobs.values():
                if job.should_run():
                    asyncio.create_task(self._execute_job(job))
            await asyncio.sleep(1.0)

    async def _execute_job(self, job: ScheduledJob) -> None:
        job.is_running = True
        job.last_run = time.monotonic()
        try:
            await job.func(*job.args, **job.kwargs)
            job.run_count += 1
            logger.info("job_executed", job_id=job.job_id, name=job.name, run_count=job.run_count)
        except Exception as e:
            logger.error("job_failed", job_id=job.job_id, name=job.name, error=str(e))
        finally:
            job.is_running = False

    def get_jobs(self) -> list[dict[str, Any]]:
        return [
            {
                "job_id": j.job_id,
                "name": j.name,
                "enabled": j.enabled,
                "interval_seconds": j.interval_seconds,
                "run_count": j.run_count,
                "last_run": j.last_run,
            }
            for j in self._jobs.values()
        ]

    def get_job(self, job_id: str) -> ScheduledJob | None:
        return self._jobs.get(job_id)
