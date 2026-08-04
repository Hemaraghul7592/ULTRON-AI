from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.tools.base import BasePlugin, BaseTool  # noqa: TC001

logger = get_logger(__name__)


class ToolRouter:
    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}
        self._plugins: dict[str, BasePlugin] = {}

    def register_plugin(self, plugin: BasePlugin) -> None:
        self._plugins[plugin.name] = plugin
        for tool in plugin.get_tools():
            self._tools[tool.name] = tool
            logger.info("tool_registered", plugin=plugin.name, tool=tool.name)

    def unregister_plugin(self, plugin_name: str) -> bool:
        plugin = self._plugins.pop(plugin_name, None)
        if not plugin:
            return False
        for tool in plugin.get_tools():
            self._tools.pop(tool.name, None)
        logger.info("plugin_unregistered", plugin=plugin_name)
        return True

    def get_tool(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def get_all_tools(self) -> list[BaseTool]:
        return list(self._tools.values())

    def get_tool_definitions(self) -> list[dict]:
        return [tool.to_definition() for tool in self._tools.values()]

    async def execute_tool(self, name: str, **kwargs: Any) -> str:
        tool = self._tools.get(name)
        if not tool:
            raise ValueError(f"Tool '{name}' not found")
        return await tool.execute(**kwargs)

    def get_plugins(self) -> list[BasePlugin]:
        return list(self._plugins.values())

    def get_plugin(self, name: str) -> BasePlugin | None:
        return self._plugins.get(name)

    async def initialize_all(self) -> None:
        for plugin in self._plugins.values():
            try:
                await plugin.initialize()
                logger.info("plugin_initialized", plugin=plugin.name)
            except Exception as e:
                logger.error("plugin_init_failed", plugin=plugin.name, error=str(e))

    async def cleanup_all(self) -> None:
        for plugin in self._plugins.values():
            try:
                await plugin.cleanup()
            except Exception as e:
                logger.error("plugin_cleanup_failed", plugin=plugin.name, error=str(e))

    def get_stats(self) -> dict[str, Any]:
        return {
            "total_plugins": len(self._plugins),
            "total_tools": len(self._tools),
            "plugins": {
                name: {
                    "tools": [t.name for t in p.get_tools()],
                    "enabled": p.is_enabled(),
                }
                for name, p in self._plugins.items()
            },
        }
