from __future__ import annotations

import re
from typing import Any

from app.agent.models import Task, TaskGraph
from app.core.logging import get_logger

logger = get_logger(__name__)

INTENT_PATTERNS: dict[str, list[str]] = {
    "search": [
        r"search\s+(for\s+)?",
        r"find\s+(information\s+)?(about\s+)?",
        r"what\s+(is|are)\s+",
        r"who\s+(is|are)\s+",
        r"look\s+up\s+",
        r"research\s+",
        r"tell\s+me\s+about\s+",
        r"explain\s+",
        r"how\s+(does|do|is|are|to)\s+",
        r"when\s+(is|was|did)\s+",
        r"where\s+(is|are)\s+",
        r"why\s+(is|are|does)\s+",
    ],
        "memory": [
            r"remember\s+",
            r"save\s+",
            r"store\s+this\s+",
            r"note\s+(that\s+)?",
            r"recall\s+",
            r"what\s+do\s+you\s+remember\s+",
            r"(my|user)\s+(profile|preference|setting)",
            r"update\s+(my|user)\s+(profile|preference)",
        ],
    "file": [
        r"\b(file|document|pdf|image|photo|picture|video|audio)\b",
        r"upload\s+",
        r"download\s+",
        r"read\s+(this|the|a)\s+(file|document)",
        r"process\s+(this|the|a)\s+(file|image|document)",
        r"ocr\s+",
        r"extract\s+(text|content)\s+(from|of)\s+",
    ],
    "plugin": [
        r"\b(github|repo|repository|issue|pr|pull.request)\b",
        r"\b(calendar|event|schedule|appointment)\b",
        r"\b(email|gmail|mail|inbox)\b",
        r"\b(drive|google.drive|spreadsheet)\b",
        r"\b(weather|forecast|temperature)\b",
        r"\b(notion|note)\b",
        r"\b(contact|people)\b",
        r"\b(map|location|address|directions)\b",
    ],
    "voice": [
        r"\b(voice|audio|speak|talk|listen|speech)\b",
        r"transcribe\s+",
        r"synthesize\s+",
    ],
    "sync": [
        r"\b(sync|synchronize|backup|restore)\b",
    ],
}


class Planner:
    def __init__(self) -> None:
        self._context: dict[str, Any] = {}

    def plan(self, user_message: str, user_id: str = "", conversation_id: str | None = None) -> TaskGraph:
        message_lower = user_message.lower().strip()
        intents = self._detect_intents(message_lower)
        graph = TaskGraph(description=user_message[:80])

        if not intents:
            intents = {"ai"}

        if "search" in intents:
            if "deep" in message_lower or "research" in message_lower:
                graph.add_task(Task(
                    name="deep_research",
                    service="search",
                    action="research",
                    args={"query": user_message, "max_results": 5, "search_depth": "advanced"},
                    priority=0,
                ))
            else:
                graph.add_task(Task(
                    name="web_search",
                    service="search",
                    action="search",
                    args={"query": user_message, "max_results": 5},
                    priority=0,
                ))

        if "memory" in intents:
            graph.add_task(Task(
                name="recall_memories",
                service="memory",
                action="get_context",
                args={"query": user_message, "user_id": user_id},
                priority=1,
            ))

            if any(w in message_lower for w in ["remember", "save", "store", "note"]):
                graph.add_task(Task(
                    name="save_to_memory",
                    service="memory",
                    action="save",
                    args={"content": user_message, "user_id": user_id, "category": "general"},
                    priority=1,
                    depends_on=[],
                ))

        if "file" in intents:
            graph.add_task(Task(
                name="file_operation",
                service="file",
                action="check_files",
                args={"query": user_message},
                priority=2,
            ))

        if "plugin" in intents:
            graph.add_task(Task(
                name="plugin_operation",
                service="plugin",
                action="execute",
                args={"query": user_message},
                priority=2,
            ))

        if "voice" in intents:
            graph.add_task(Task(
                name="voice_interaction",
                service="voice",
                action="process",
                args={"query": user_message},
                priority=1,
            ))

        if "sync" in intents:
            graph.add_task(Task(
                name="sync_operation",
                service="sync",
                action="sync",
                args={"query": user_message},
                priority=3,
            ))

        ai_priority = 10
        deps = [t.id for t in graph.tasks.values() if t.service != "ai"]
        graph.add_task(Task(
            name="ai_response",
            service="ai",
            action="chat",
            args={
                "message": user_message,
                "use_tools": True,
                "use_memory": "memory" in intents,
            },
            priority=ai_priority,
            depends_on=deps,
        ))

        logger.info(
            "plan_created",
            intents=list(intents),
            task_count=graph.size(),
            graph_id=graph.id,
        )
        return graph

    def _detect_intents(self, message: str) -> set[str]:
        intents: set[str] = set()
        for intent, patterns in INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, message):
                    intents.add(intent)
                    break
        return intents
