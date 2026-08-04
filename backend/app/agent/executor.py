from __future__ import annotations

import asyncio
import builtins
import time
from typing import TYPE_CHECKING, Any

from app.agent.context import AgentContext  # noqa: TC001
from app.agent.errors import DependencyError, ExecutionError, RecoveryError
from app.core.logging import get_logger

if TYPE_CHECKING:
    from app.agent.models import Task, TaskGraph

logger = get_logger(__name__)

DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 2


class Executor:
    def __init__(
        self,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> None:
        self._timeout = timeout
        self._max_retries = max_retries
        self._handlers: dict[str, Any] = {}

    def register_handler(self, service: str, handler: Any) -> None:
        self._handlers[service] = handler

    async def execute(self, graph: TaskGraph, context: AgentContext) -> AgentContext:
        completed_ids: set[str] = set()
        max_rounds = graph.size() * (self._max_retries + 1)
        round_count = 0

        while not graph.is_complete() and round_count < max_rounds:
            round_count += 1
            ready = graph.get_ready_tasks(completed_ids)

            if not ready and not graph.is_complete():
                pending = [t.id for t in graph.tasks.values() if t.status == "pending"]
                if pending:
                    raise DependencyError(
                        message=f"Deadlock: {len(pending)} tasks waiting for unsatisfied deps",
                        task_id=pending[0],
                    )
                break

            for task in ready:
                await self._execute_task(task, graph, context)
                if task.status in ("completed", "failed"):
                    completed_ids.add(task.id)

            await asyncio.sleep(0)

        return context

    async def execute_sequential(self, task: Task, graph: TaskGraph, context: AgentContext) -> Any:
        await self._execute_task(task, graph, context)
        return task.result

    async def _execute_task(
        self,
        task: Task,
        graph: TaskGraph,
        context: AgentContext,
    ) -> None:
        task.status = "in_progress"
        task.started_at = time.time()
        start = time.monotonic()

        try:
            handler = self._handlers.get(task.service)
            if handler is None:
                raise ExecutionError(
                    message=f"No handler for service '{task.service}'",
                    task_id=task.id,
                )

            task.result = await asyncio.wait_for(
                handler(task, context),
                timeout=self._timeout,
            )

            task.status = "completed"
            graph.mark_completed(task.id)

        except builtins.TimeoutError:
            task.status = "failed"
            task.error = f"Timeout after {self._timeout}s"
            graph.mark_failed(task.id, task.error)
            logger.error("task_timeout", task=task.name, timeout=self._timeout)

        except Exception as e:
            if task.can_retry():
                graph.mark_retry(task.id)
                logger.warning(
                    "task_retry", task=task.name, attempt=task.attempts, error=type(e).__name__,
                )
            else:
                task.status = "failed"
                task.error = type(e).__name__
                graph.mark_failed(task.id, task.error)
                logger.error("task_failed", task=task.name, error=type(e).__name__)

        finally:
            duration_ms = (time.monotonic() - start) * 1000
            context.log(task, result=task.result, error=task.error, duration_ms=duration_ms)

    async def recover(
        self,
        task: Task,
        graph: TaskGraph,
        recovery_action: str = "retry",
    ) -> None:
        if recovery_action == "retry":
            task.attempts = 0
            graph.mark_retry(task.id)
        elif recovery_action == "skip":
            graph.mark_completed(task.id)
        elif recovery_action == "fail":
            graph.mark_failed(task.id, "Recovery failed")
        else:
            raise RecoveryError(
                message=f"Unknown recovery action: {recovery_action}",
                task_id=task.id,
            )
