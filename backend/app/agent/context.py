from __future__ import annotations

import time
from typing import Any

from app.agent.models import Task  # noqa: TC001


class AgentContext:
    def __init__(self, request_id: str = "") -> None:
        self.request_id = request_id
        self.conversation_id: str | None = None
        self.user_id: str = ""
        self.user_message: str = ""
        self.memory_refs: list[str] = []
        self.search_results: dict[str, Any] = {}
        self.file_refs: list[str] = []
        self.plugin_results: dict[str, Any] = {}
        self.voice_session_id: str | None = None
        self.sync_state: dict[str, Any] = {}
        self.execution_log: list[dict[str, Any]] = []
        self.created_at = time.time()

    def log(
        self,
        task: Task,
        result: Any = None,
        error: str = "",
        duration_ms: float = 0.0,
    ) -> None:
        self.execution_log.append(
            {
                "task_id": task.id,
                "task_name": task.name,
                "service": task.service,
                "action": task.action,
                "status": task.status,
                "result": str(result)[:500] if result else "",
                "error": error,
                "duration_ms": round(duration_ms, 2),
                "attempts": task.attempts,
            },
        )

    def get_execution_summary(self) -> dict[str, Any]:
        completed = sum(1 for e in self.execution_log if e["status"] == "completed")
        failed = sum(1 for e in self.execution_log if e["status"] == "failed")
        return {
            "request_id": self.request_id,
            "total_tasks": len(self.execution_log),
            "completed": completed,
            "failed": failed,
            "conversation_id": self.conversation_id,
            "memory_refs": self.memory_refs,
            "file_refs": self.file_refs,
            "duration_s": round(time.time() - self.created_at, 2),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "conversation_id": self.conversation_id,
            "user_id": self.user_id,
            "memory_refs": self.memory_refs,
            "search_results": self.search_results,
            "file_refs": self.file_refs,
            "plugin_results": self.plugin_results,
            "voice_session_id": self.voice_session_id,
            "execution_log": self.execution_log,
        }
