from __future__ import annotations

import os
from typing import TYPE_CHECKING

from app.operations.incidents.domain.enums import EvidenceCategory
from app.operations.incidents.infrastructure.collectors.base import BaseCollector

if TYPE_CHECKING:
    from app.operations.incidents.domain.models import Incident, IncidentEvidence


class FastAPILogCollector(BaseCollector):
    name = "fastapi_logs"
    category = EvidenceCategory.LOG

    def __init__(self, log_path: str | None = None) -> None:
        self._log_path = log_path

    async def collect(self, incident: Incident) -> IncidentEvidence:
        log_path = self._log_path or self._find_log_file()
        if not log_path or not os.path.exists(log_path):
            return self._safe_build(
                incident,
                source=self.name,
                payload_ref=log_path or "not_found",
                content="FastAPI log file not found",
            )
        try:
            with open(log_path) as f:
                lines = f.readlines()[-200:]
            content = "".join(lines)
            return self._safe_build(
                incident,
                source=self.name,
                payload_ref=log_path,
                content=content,
                metadata={"lines_searched": "200"},
            )
        except OSError as exc:
            return self._safe_build(
                incident,
                source=self.name,
                payload_ref=log_path,
                content=f"Error reading log file: {exc}",
            )

    def _find_log_file(self) -> str | None:
        candidates = [
            os.environ.get("ULTRON_LOG_FILE"),
            "/var/log/ultron/app.log",
            "/app/logs/app.log",
            "logs/app.log",
        ]
        for candidate in candidates:
            if candidate and os.path.exists(candidate):
                return candidate
        return None


class StackTraceCollector(BaseCollector):
    name = "stack_traces"
    category = EvidenceCategory.LOG

    def __init__(self) -> None:
        self._captured_traces: list[str] = []

    def capture(self, exc: BaseException, context: str = "") -> None:
        import traceback

        trace_str = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        if context:
            trace_str = f"[{context}] {trace_str}"
        self._captured_traces.append(trace_str)

    async def collect(self, incident: Incident) -> IncidentEvidence:
        if not self._captured_traces:
            return self._safe_build(
                incident,
                source=self.name,
                payload_ref="no_traces",
                content="No stack traces captured for this incident",
            )
        content = "\n---\n".join(self._captured_traces[-10:])
        return self._safe_build(
            incident,
            source=self.name,
            payload_ref="captured_traces",
            content=content,
            metadata={"trace_count": str(len(self._captured_traces))},
        )


class StructuredLogCollector(BaseCollector):
    name = "structured_logs"
    category = EvidenceCategory.LOG

    def __init__(self) -> None:
        self._entries: list[str] = []

    def add(self, entry: str) -> None:
        self._entries.append(entry)

    async def collect(self, incident: Incident) -> IncidentEvidence:
        if not self._entries:
            return self._safe_build(
                incident,
                source=self.name,
                payload_ref="no_entries",
                content="No structured log entries captured",
            )
        content = "\n".join(self._entries[-200:])
        return self._safe_build(
            incident,
            source=self.name,
            payload_ref="structured_logs",
            content=content,
            metadata={"entry_count": str(len(self._entries))},
        )


class SchedulerLogCollector(BaseCollector):
    name = "scheduler_logs"
    category = EvidenceCategory.LOG

    def __init__(self) -> None:
        self._logs: list[str] = []

    def add(self, log: str) -> None:
        self._logs.append(log)

    async def collect(self, incident: Incident) -> IncidentEvidence:
        if not self._logs:
            return self._safe_build(
                incident,
                source=self.name,
                payload_ref="no_logs",
                content="No scheduler log entries captured",
            )
        content = "\n".join(self._logs[-100:])
        return self._safe_build(
            incident,
            source=self.name,
            payload_ref="scheduler_logs",
            content=content,
            metadata={"log_count": str(len(self._logs))},
        )
