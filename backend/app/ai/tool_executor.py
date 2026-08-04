from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from app.core.exceptions import ToolExecutionException
from app.core.logging import get_logger

if TYPE_CHECKING:
    from app.plugins.manager import PluginManager

logger = get_logger(__name__)


class ToolExecutor:
    def __init__(self) -> None:
        self._tools: dict[str, Any] = {}
        self._plugin_manager: PluginManager | None = None

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

    def sync_from_plugin_manager(self, plugin_manager: PluginManager) -> None:
        self._plugin_manager = plugin_manager
        self._tools.clear()
        for tool_def in plugin_manager.get_all_tools():
            name = tool_def["name"]
            self._tools[name] = {
                "handler": self._create_plugin_handler(name),
                "description": tool_def["description"],
                "parameters": tool_def["parameters"],
            }
        logger.info("tools_synced_from_plugin_manager", count=len(self._tools))

    def _create_plugin_handler(self, tool_name: str) -> Any:
        async def handler(**kwargs: Any) -> str:
            pm = self._plugin_manager
            if pm is None:
                raise ToolExecutionException(
                    tool_name=tool_name,
                    message="PluginManager not available",
                )
            user_id = kwargs.pop("user_id", None)
            result = await pm.execute_tool_safe(tool_name, user_id=user_id, **kwargs)
            if result.get("success"):
                return result.get("result", "")
            raise ToolExecutionException(
                tool_name=tool_name,
                message=result.get("error", "Unknown error"),
            )

        return handler

    def get_tool_definitions(self) -> list[dict[str, Any]]:
        definitions = []
        for name, tool in self._tools.items():
            definitions.append(
                {
                    "type": "function",
                    "function": {
                        "name": name,
                        "description": tool["description"],
                        "parameters": tool["parameters"],
                    },
                },
            )
        return definitions

    async def execute(
        self,
        tool_call: dict[str, Any],
        user_id: str | None = None,
    ) -> dict[str, Any]:
        name = tool_call.get("name", "")
        arguments = tool_call.get("arguments", {})
        if any(key in arguments for key in ("user_id", "userId", "owner_id", "ownerId")):
            raise ToolExecutionException(
                tool_name=name,
                message="Caller identity is not an accepted tool argument",
            )
        if user_id is not None:
            arguments = {**arguments, "user_id": user_id}
        tool_call_id = tool_call.get("id", "")

        if name not in self._tools:
            raise ToolExecutionException(
                tool_name=name,
                message="Tool not found",
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
                "error": "Tool execution failed",
                "execution_time_ms": execution_time,
            }

    async def execute_multiple(
        self,
        tool_calls: list[dict[str, Any]],
        user_id: str | None = None,
    ) -> list[dict[str, Any]]:
        results = []
        for tc in tool_calls:
            result = await self.execute(tc, user_id=user_id)
            results.append(result)
        return results

    def has_tools(self) -> bool:
        return len(self._tools) > 0

    def get_tool_names(self) -> list[str]:
        return list(self._tools.keys())
