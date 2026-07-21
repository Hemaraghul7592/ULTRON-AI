from __future__ import annotations

import time
import uuid
from typing import Any, Callable, Optional


class Task:
    def __init__(
        self,
        name: str,
        service: str,
        action: str,
        args: dict[str, Any] | None = None,
        priority: int = 0,
        max_retries: int = 2,
        depends_on: list[str] | None = None,
    ) -> None:
        self.id = str(uuid.uuid4())[:8]
        self.name = name
        self.service = service
        self.action = action
        self.args = args or {}
        self.priority = priority
        self.max_retries = max_retries
        self.depends_on = depends_on or []
        self.status: str = "pending"
        self.result: Any = None
        self.error: str = ""
        self.attempts = 0
        self.started_at: float = 0.0
        self.completed_at: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "service": self.service,
            "action": self.action,
            "args": self.args,
            "priority": self.priority,
            "max_retries": self.max_retries,
            "depends_on": self.depends_on,
            "status": self.status,
            "error": self.error,
            "attempts": self.attempts,
        }

    def is_ready(self, completed_ids: set[str]) -> bool:
        if self.status != "pending":
            return False
        return all(dep in completed_ids for dep in self.depends_on)

    def can_retry(self) -> bool:
        return self.attempts < self.max_retries


class TaskGraph:
    def __init__(self, description: str = "") -> None:
        self.id = str(uuid.uuid4())[:8]
        self.description = description
        self.tasks: dict[str, Task] = {}
        self._order: list[str] = []

    def add_task(self, task: Task) -> None:
        self.tasks[task.id] = task
        self._order.append(task.id)

    def add_tasks(self, tasks: list[Task]) -> None:
        for t in tasks:
            self.add_task(t)

    def get_ready_tasks(self, completed_ids: set[str]) -> list[Task]:
        ready = [t for t in self.tasks.values() if t.is_ready(completed_ids)]
        ready.sort(key=lambda t: (-t.priority, self._order.index(t.id)))
        return ready

    def get_next_ready(self, completed_ids: set[str]) -> Task | None:
        ready = self.get_ready_tasks(completed_ids)
        return ready[0] if ready else None

    def is_complete(self) -> bool:
        return all(t.status in ("completed", "failed") for t in self.tasks.values())

    def all_succeeded(self) -> bool:
        return all(t.status == "completed" for t in self.tasks.values())

    def mark_completed(self, task_id: str) -> None:
        if task_id in self.tasks:
            self.tasks[task_id].status = "completed"
            self.tasks[task_id].completed_at = time.time()

    def mark_failed(self, task_id: str, error: str) -> None:
        if task_id in self.tasks:
            self.tasks[task_id].status = "failed"
            self.tasks[task_id].error = error

    def mark_retry(self, task_id: str) -> None:
        if task_id in self.tasks:
            self.tasks[task_id].attempts += 1
            self.tasks[task_id].status = "pending"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "tasks": [t.to_dict() for t in self.tasks.values()],
        }

    def size(self) -> int:
        return len(self.tasks)
