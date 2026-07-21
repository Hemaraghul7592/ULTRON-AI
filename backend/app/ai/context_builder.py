from __future__ import annotations

from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


class ContextBuilder:
    def __init__(self) -> None:
        self._max_context_tokens: int = 12000
        self._reserved_tokens: int = 4096

    def build_context(
        self,
        memories: list[dict[str, Any]] | None = None,
        recent_messages: list[dict[str, str]] | None = None,
        entities: list[dict[str, Any]] | None = None,
        task_context: list[dict[str, Any]] | None = None,
        current_time: str | None = None,
    ) -> str:
        parts: list[str] = []

        if current_time:
            parts.append(f"Current time: {current_time}")

        if memories:
            memory_texts = []
            for mem in memories[:10]:
                content = mem.get("content", "")
                importance = mem.get("importance", 0.5)
                tags = mem.get("tags", [])
                tag_str = ", ".join(tags) if tags else ""
                memory_texts.append(
                    f"- [{importance:.1f}] {content}" + (f" ({tag_str})" if tag_str else ""),
                )
            parts.append("Relevant memories:\n" + "\n".join(memory_texts))

        if entities:
            entity_texts = []
            for ent in entities[:5]:
                name = ent.get("name", "")
                etype = ent.get("entity_type", "")
                desc = ent.get("description", "")
                entity_texts.append(f"- {name} ({etype}): {desc}")
            parts.append("Known entities:\n" + "\n".join(entity_texts))

        if task_context:
            task_texts = []
            for task in task_context[:5]:
                title = task.get("title", "")
                status = task.get("status", "")
                due = task.get("due_date", "")
                task_texts.append(f"- {title} [{status}]" + (f" (due: {due})" if due else ""))
            parts.append("Active tasks:\n" + "\n".join(task_texts))

        return "\n\n".join(parts) if parts else ""

    def estimate_tokens(self, text: str) -> int:
        return len(text) // 4

    def truncate_to_fit(
        self,
        messages: list[dict[str, Any]],
        max_tokens: int | None = None,
    ) -> list[dict[str, Any]]:
        limit = max_tokens or (self._max_context_tokens - self._reserved_tokens)
        total = 0
        result: list[dict[str, Any]] = []

        system_msgs = [m for m in messages if m.get("role") == "system"]
        other_msgs = [m for m in messages if m.get("role") != "system"]

        for msg in system_msgs:
            tokens = self.estimate_tokens(msg.get("content", ""))
            total += tokens
            result.append(msg)

        for msg in reversed(other_msgs):
            tokens = self.estimate_tokens(msg.get("content", ""))
            if total + tokens > limit:
                break
            total += tokens
            result.insert(len(system_msgs), msg)

        return result

    def format_memory_context(self, memories: list[dict[str, Any]]) -> str:
        if not memories:
            return ""
        lines = []
        for mem in memories:
            content = mem.get("content", "")
            mem_type = mem.get("memory_type", "unknown")
            importance = mem.get("importance", 0.5)
            lines.append(f"[{mem_type}/{importance:.1f}] {content}")
        return "\n".join(lines)
