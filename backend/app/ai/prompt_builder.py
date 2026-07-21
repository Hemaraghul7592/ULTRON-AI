from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)

DEFAULT_SYSTEM_PROMPT = """You are ULTRON, a powerful and intelligent personal AI assistant.
You are helpful, accurate, and efficient. You have access to various tools and can help with:
- Answering questions and providing information
- Managing tasks, reminders, and schedules
- Searching the web and retrieving information
- Working with files, documents, and data
- Automating workflows and processes
- Managing email, calendar, and productivity tools

Be concise, direct, and helpful. Always prioritize accuracy over verbosity.
If you're unsure about something, say so rather than guessing.
When using tools, explain what you're doing briefly."""


class PromptBuilder:
    def __init__(self) -> None:
        self._system_prompt = DEFAULT_SYSTEM_PROMPT

    def set_system_prompt(self, prompt: str) -> None:
        self._system_prompt = prompt

    def build_messages(
        self,
        user_message: str,
        conversation_history: list[dict[str, str]] | None = None,
        system_prompt: str | None = None,
        memory_context: str | None = None,
        tool_results: list[dict[str, Any]] | None = None,
        additional_context: str | None = None,
    ) -> list[dict[str, Any]]:
        messages: list[dict[str, Any]] = []

        system_parts = [system_prompt or self._system_prompt]

        if memory_context:
            system_parts.append(f"\n\nRelevant memories:\n{memory_context}")

        if additional_context:
            system_parts.append(f"\n\nAdditional context:\n{additional_context}")

        system_parts.append(
            f"\n\nCurrent time: {datetime.now(timezone.utc).isoformat()}"
        )

        messages.append({"role": "system", "content": "\n".join(system_parts)})

        if conversation_history:
            for msg in conversation_history[-20:]:
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", ""),
                })

        if tool_results:
            for tr in tool_results:
                messages.append({
                    "role": "tool",
                    "content": f"Tool {tr['name']} result: {tr['result']}",
                    "tool_call_id": tr.get("tool_call_id", ""),
                })

        messages.append({"role": "user", "content": user_message})
        return messages

    def build_with_tool_calls(
        self,
        messages: list[dict[str, Any]],
        tool_call_results: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        for result in tool_call_results:
            messages.append({
                "role": "tool",
                "content": result.get("result", ""),
                "tool_call_id": result.get("tool_call_id", ""),
            })
        return messages

    def build_summary_prompt(self, texts: list[str]) -> str:
        combined = "\n\n".join(texts)
        return (
            "Summarize the following conversations concisely, capturing key topics, "
            "decisions, and action items:\n\n"
            f"{combined}"
        )

    def build_memory_extraction_prompt(self, text: str) -> str:
        return (
            "Extract important facts, preferences, relationships, and decisions "
            "from the following text. Return them as a JSON array of objects with "
            "'content', 'importance' (0-1), 'type' (fact/preference/decision/context), "
            "and 'tags' fields:\n\n"
            f"{text}"
        )

    def build_entity_extraction_prompt(self, text: str) -> str:
        return (
            "Extract all named entities (people, places, organizations, concepts) "
            "and their relationships from the following text. Return as JSON with "
            "'entities' (name, type, description) and 'relationships' (source, target, type, weight):\n\n"
            f"{text}"
        )
