from __future__ import annotations

import uuid
from typing import Any

from app.agent.context import AgentContext
from app.agent.executor import Executor
from app.agent.models import TaskGraph
from app.agent.planner import Planner
from app.core.logging import get_logger

logger = get_logger(__name__)


class AgentService:
    def __init__(self) -> None:
        self._planner = Planner()
        self._executor = Executor()
        self._service_registry: dict[str, Any] = {}

    @property
    def executor(self) -> Executor:
        return self._executor

    def register_service(self, name: str, handler: Any) -> None:
        self._service_registry[name] = handler
        self._executor.register_handler(name, handler)
        logger.info("agent_service_registered", service=name)

    async def process(
        self,
        user_message: str,
        user_id: str = "",
        conversation_id: str | None = None,
        context: AgentContext | None = None,
    ) -> dict[str, Any]:
        request_id = str(uuid.uuid4())[:8]
        ctx = context or AgentContext(request_id=request_id)
        ctx.user_message = user_message
        ctx.user_id = user_id
        ctx.conversation_id = conversation_id

        graph = self._planner.plan(user_message, user_id, conversation_id)

        ctx = await self._executor.execute(graph, ctx)

        summary = ctx.get_execution_summary()
        summary["graph_id"] = graph.id
        summary["success"] = graph.all_succeeded()

        logger.info(
            "agent_run_complete",
            request_id=request_id,
            success=graph.all_succeeded(),
            tasks=graph.size(),
        )

        return summary

    async def process_with_callback(
        self,
        user_message: str,
        user_id: str = "",
        callback: Any = None,
    ) -> dict[str, Any]:
        result = await self.process(user_message, user_id)
        if callback:
            callback(result)
        return result

    def get_execution_log(self) -> list[dict[str, Any]]:
        return []

    async def health_check(self) -> dict[str, Any]:
        return {
            "status": "healthy",
            "registered_services": list(self._service_registry.keys()),
        }
