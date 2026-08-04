from __future__ import annotations

import asyncio
import time
from collections.abc import Callable, Coroutine  # noqa: TC003
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


class WorkerTask:
    def __init__(
        self,
        task_id: str,
        name: str,
        func: Callable[..., Coroutine[Any, Any, Any]],
        args: tuple = (),
        kwargs: dict | None = None,
        priority: int = 0,
    ) -> None:
        self.task_id = task_id
        self.name = name
        self.func = func
        self.args = args
        self.kwargs = kwargs or {}
        self.priority = priority
        self.status: str = "pending"
        self.result: Any = None
        self.error: str | None = None
        self.created_at: float = time.monotonic()
        self.started_at: float | None = None
        self.completed_at: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "name": self.name,
            "status": self.status,
            "priority": self.priority,
            "result": str(self.result) if self.result else None,
            "error": self.error,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }


class BackgroundWorker:
    def __init__(self, max_concurrent: int = 5) -> None:
        self._max_concurrent = max_concurrent
        self._queue: asyncio.PriorityQueue[tuple[int, WorkerTask]] = asyncio.PriorityQueue()
        self._running = False
        self._workers: list[asyncio.Task] = []
        self._active_tasks: dict[str, WorkerTask] = {}
        self._completed_tasks: dict[str, WorkerTask] = {}
        self._task_id_counter: int = 0

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        for i in range(self._max_concurrent):
            worker = asyncio.create_task(self._worker_loop(f"worker-{i}"))
            self._workers.append(worker)
        logger.info("background_worker_started", workers=self._max_concurrent)

    async def stop(self) -> None:
        self._running = False
        for worker in self._workers:
            worker.cancel()
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()
        logger.info("background_worker_stopped")

    def submit(
        self,
        name: str,
        func: Callable[..., Coroutine[Any, Any, Any]],
        args: tuple = (),
        kwargs: dict | None = None,
        priority: int = 0,
    ) -> str:
        self._task_id_counter += 1
        task_id = f"task-{self._task_id_counter}"
        task = WorkerTask(
            task_id=task_id,
            name=name,
            func=func,
            args=args,
            kwargs=kwargs,
            priority=priority,
        )
        self._active_tasks[task_id] = task
        self._queue.put_nowait((-priority, task))
        logger.info("task_submitted", task_id=task_id, name=name, priority=priority)
        return task_id

    async def _worker_loop(self, worker_name: str) -> None:
        while self._running:
            try:
                _, task = await asyncio.wait_for(self._queue.get(), timeout=1.0)
            except TimeoutError:
                continue
            except asyncio.CancelledError:
                return

            task.status = "running"
            task.started_at = time.monotonic()
            logger.info("task_started", worker=worker_name, task_id=task.task_id)

            try:
                result = await task.func(*task.args, **task.kwargs)
                task.result = result
                task.status = "completed"
            except Exception as e:
                task.error = str(e)
                task.status = "failed"
                logger.error("task_failed", task_id=task.task_id, error=str(e))
            finally:
                task.completed_at = time.monotonic()
                self._active_tasks.pop(task.task_id, None)
                self._completed_tasks[task.task_id] = task
                elapsed = (task.completed_at - task.started_at) * 1000 if task.started_at else 0
                logger.info(
                    "task_completed",
                    worker=worker_name,
                    task_id=task.task_id,
                    status=task.status,
                    elapsed_ms=elapsed,
                )

    def get_task(self, task_id: str) -> WorkerTask | None:
        return self._active_tasks.get(task_id) or self._completed_tasks.get(task_id)

    def get_active_tasks(self) -> list[dict[str, Any]]:
        return [t.to_dict() for t in self._active_tasks.values()]

    def get_stats(self) -> dict[str, Any]:
        return {
            "queue_size": self._queue.qsize(),
            "active_count": len(self._active_tasks),
            "completed_count": len(self._completed_tasks),
            "max_concurrent": self._max_concurrent,
            "running": self._running,
        }
