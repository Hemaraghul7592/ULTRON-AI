from __future__ import annotations

import json
import time
from typing import Any

from app.core.exceptions import ToolExecutionException
from app.core.logging import get_logger

logger = get_logger(__name__)


class ToolExecutor:
    def __init__(self) -> None:
        self._tools: dict[str, Any] = {}

    def register_tool(
        self,
        name: str,
        handler: Any,
        description: str = "",
        parameters: dict | None = None,
    ) -> None:
        self._tools[name] = {
            "handler": handler,
            "description": description,
            "parameters": parameters or {},
        }
        logger.info("tool_registered", name=name)

    def get_tool_definitions(self) -> list[dict[str, Any]]:
        definitions = []
        for name, tool in self._tools.items():
            definitions.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": tool["description"],
                    "parameters": tool["parameters"],
                },
            })
        return definitions

    async def execute(self, tool_call: dict[str, Any]) -> dict[str, Any]:
        name = tool_call.get("name", "")
        arguments = tool_call.get("arguments", {})
        tool_call_id = tool_call.get("id", "")

        if name not in self._tools:
            raise ToolExecutionException(
                tool_name=name, message="Tool not found"
            )

        tool = self._tools[name]
        handler = tool["handler"]
        start = time.monotonic()

        try:
            if callable(handler):
                import inspect
                if inspect.iscoroutinefunction(handler):
                    result = await handler(**arguments)
                else:
                    result = handler(**arguments)
            else:
                result = str(handler)

            execution_time = (time.monotonic() - start) * 1000
            logger.info(
                "tool_executed",
                name=name,
                execution_time_ms=execution_time,
                success=True,
            )
            return {
                "tool_call_id": tool_call_id,
                "name": name,
                "result": str(result),
                "success": True,
                "execution_time_ms": execution_time,
            }
        except ToolExecutionException:
            raise
        except Exception as e:
            execution_time = (time.monotonic() - start) * 1000
            logger.error(
                "tool_execution_failed",
                name=name,
                error=str(e),
                execution_time_ms=execution_time,
            )
            return {
                "tool_call_id": tool_call_id,
                "name": name,
                "result": "",
                "success": False,
                "error": str(e),
                "execution_time_ms": execution_time,
            }

    async def execute_multiple(
        self, tool_calls: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        results = []
        for tc in tool_calls:
            result = await self.execute(tc)
            results.append(result)
        return results

    def has_tools(self) -> bool:
        return len(self._tools) > 0

    def get_tool_names(self) -> list[str]:
        return list(self._tools.keys())
