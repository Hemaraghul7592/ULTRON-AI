from __future__ import annotations

import importlib
from typing import Any

from app.core.logging import get_logger
from app.tools.base import BasePlugin
from app.tools.router import ToolRouter

logger = get_logger(__name__)

BUILTIN_PLUGINS: list[str] = [
    "app.plugins.weather",
    "app.plugins.google_drive",
    "app.plugins.github_plugin",
    "app.plugins.notion_plugin",
    "app.plugins.ocr_plugin",
    "app.plugins.gmail_plugin",
    "app.plugins.calendar_plugin",
    "app.plugins.google_maps_plugin",
    "app.plugins.tavily_plugin",
    "app.plugins.people_plugin",
]


class PluginLoader:
    def __init__(self, tool_router: ToolRouter) -> None:
        self.tool_router = tool_router
        self._loaded_plugins: dict[str, BasePlugin] = {}

    async def load_builtin_plugins(self) -> int:
        loaded = 0
        for plugin_module in BUILTIN_PLUGINS:
            try:
                plugin = await self._load_plugin(plugin_module)
                if plugin:
                    self.tool_router.register_plugin(plugin)
                    self._loaded_plugins[plugin.name] = plugin
                    loaded += 1
            except Exception as e:
                logger.error("builtin_plugin_load_failed", module=plugin_module, error=str(e))
        logger.info("builtin_plugins_loaded", count=loaded)
        return loaded

    async def load_plugin(self, module_path: str) -> BasePlugin | None:
        plugin = await self._load_plugin(module_path)
        if plugin:
            self.tool_router.register_plugin(plugin)
            self._loaded_plugins[plugin.name] = plugin
        return plugin

    async def _load_plugin(self, module_path: str) -> BasePlugin | None:
        try:
            module = importlib.import_module(module_path)
            plugin_class = getattr(module, "Plugin", None)
            if plugin_class and issubclass(plugin_class, BasePlugin):
                plugin = plugin_class()
                await plugin.initialize()
                logger.info("plugin_loaded", module=module_path, name=plugin.name)
                return plugin
            logger.warning("no_plugin_class_found", module=module_path)
            return None
        except ImportError as e:
            logger.error("plugin_import_failed", module=module_path, error=str(e))
            return None

    async def unload_plugin(self, plugin_name: str) -> bool:
        plugin = self._loaded_plugins.pop(plugin_name, None)
        if plugin:
            await plugin.cleanup()
            self.tool_router.unregister_plugin(plugin_name)
            return True
        return False

    async def reload_plugin(self, module_path: str) -> BasePlugin | None:
        module = importlib.import_module(module_path)
        if hasattr(module, "Plugin"):
            plugin_class = module.Plugin
            old_plugin = None
            for p in self._loaded_plugins.values():
                if type(p).__module__ == module_path:
                    old_plugin = p
                    break
            if old_plugin:
                await self.unload_plugin(old_plugin.name)

        return await self.load_plugin(module_path)

    def get_loaded_plugins(self) -> list[dict[str, Any]]:
        return [
            {
                "name": p.name,
                "version": p.version,
                "description": p.description,
                "tools": [t.name for t in p.get_tools()],
            }
            for p in self._loaded_plugins.values()
        ]
