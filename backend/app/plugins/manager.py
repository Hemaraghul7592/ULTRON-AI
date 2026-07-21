from __future__ import annotations

import time
from typing import Any

from app.core.logging import get_logger
from app.plugins.base import PluginInterface, PluginMetadata, PluginStatus
from app.plugins.errors import (
    PluginAuthError,
    PluginError,
    PluginNotFoundError,
    PluginUnavailableError,
    error_response,
    normalize_error,
    success_response,
)
from app.tools.plugin_loader import BUILTIN_PLUGINS, PluginLoader
from app.tools.router import ToolRouter

logger = get_logger(__name__)


class PluginManager:
    def __init__(self) -> None:
        self._router = ToolRouter()
        self._loader = PluginLoader(self._router)
        self._statuses: dict[str, str] = {}
        self._health_cache: dict[str, PluginMetadata] = {}
        self._initialized = False

    async def initialize(self) -> int:
        count = await self._loader.load_builtin_plugins()
        for name, plugin in self._router._plugins.items():
            self._statuses[name] = PluginStatus.INITIALIZED
            self._health_cache[name] = PluginInterface.get_metadata(plugin)
        self._initialized = True
        logger.info("plugin_manager_initialized", plugins=count)
        return count

    async def shutdown(self) -> None:
        await self._router.cleanup_all()
        self._router._plugins.clear()
        self._router._tools.clear()
        self._statuses.clear()
        self._health_cache.clear()
        self._initialized = False
        logger.info("plugin_manager_shutdown")

    def is_initialized(self) -> bool:
        return self._initialized

    def get_plugin(self, name: str) -> PluginInterface | None:
        plugin = self._router.get_plugin(name)
        if plugin is not None and isinstance(plugin, PluginInterface):
            return plugin
        return None

    def get_all_plugins(self) -> list[PluginInterface]:
        result: list[PluginInterface] = []
        for plugin in self._router.get_plugins():
            if isinstance(plugin, PluginInterface):
                result.append(plugin)
        return result

    def get_tool_definitions(self) -> list[dict[str, Any]]:
        return self._router.get_tool_definitions()

    def get_all_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters,
                "plugin": self._find_plugin_for_tool(t.name),
            }
            for t in self._router.get_all_tools()
        ]

    def plugin_count(self) -> int:
        return len(self._router._plugins)

    def tool_count(self) -> int:
        return len(self._router._tools)

    def _find_plugin_for_tool(self, tool_name: str) -> str:
        for pname, plugin in self._router._plugins.items():
            for tool in plugin.get_tools():
                if tool.name == tool_name:
                    return pname
        return ""

    def get_status(self, plugin_name: str) -> str | None:
        return self._statuses.get(plugin_name)

    def set_status(self, plugin_name: str, status: str) -> None:
        self._statuses[plugin_name] = status

    def get_all_statuses(self) -> dict[str, str]:
        return dict(self._statuses)

    async def health_check(self, plugin_name: str | None = None) -> dict[str, Any]:
        if plugin_name:
            plugin = self.get_plugin(plugin_name)
            if plugin is None:
                return {"plugin": plugin_name, "status": PluginStatus.UNAVAILABLE, "error": "not_found"}
            try:
                health = await plugin.health_check()
                self._statuses[plugin_name] = health.get("status", PluginStatus.AVAILABLE)
                return {"plugin": plugin_name, **health}
            except Exception as e:
                self._statuses[plugin_name] = PluginStatus.ERROR
                return {"plugin": plugin_name, "status": PluginStatus.ERROR, "error": str(e)}
        else:
            results: dict[str, Any] = {
                "healthy": 0,
                "degraded": 0,
                "unavailable": 0,
                "plugins": {},
            }
            for plugin in self.get_all_plugins():
                try:
                    health = await plugin.health_check()
                    status = health.get("status", PluginStatus.AVAILABLE)
                    self._statuses[plugin.name] = status
                    if status == PluginStatus.AVAILABLE:
                        results["healthy"] += 1
                    elif status == PluginStatus.UNAVAILABLE:
                        results["unavailable"] += 1
                    else:
                        results["degraded"] += 1
                    results["plugins"][plugin.name] = health
                except Exception as e:
                    self._statuses[plugin.name] = PluginStatus.ERROR
                    results["unavailable"] += 1
                    results["plugins"][plugin.name] = {"status": PluginStatus.ERROR, "error": str(e)}
            return results

    async def execute_tool(
        self, tool_name: str, **kwargs: Any
    ) -> dict[str, Any]:
        plugin_name = self._find_plugin_for_tool(tool_name)

        try:
            tool = self._router.get_tool(tool_name)
            if tool is None:
                raise PluginNotFoundError(
                    message=f"Tool '{tool_name}' not found",
                    plugin_name=plugin_name,
                )

            status = self._statuses.get(plugin_name)
            if status in (PluginStatus.DISABLED, PluginStatus.AUTH_FAILED, PluginStatus.UNAVAILABLE):
                raise PluginUnavailableError(
                    message=f"Plugin '{plugin_name}' is {status}",
                    plugin_name=plugin_name,
                )

            result = await tool.execute(**kwargs)
            self._statuses[plugin_name] = PluginStatus.AVAILABLE
            return success_response(result=str(result), tool_name=tool_name, plugin_name=plugin_name)

        except PluginError:
            self._statuses[plugin_name] = PluginStatus.ERROR
            raise
        except Exception as e:
            self._statuses[plugin_name] = PluginStatus.ERROR
            normalized = normalize_error(e, plugin_name)
            raise normalized

    async def execute_tool_safe(
        self, tool_name: str, **kwargs: Any
    ) -> dict[str, Any]:
        try:
            return await self.execute_tool(tool_name, **kwargs)
        except PluginNotFoundError as e:
            return error_response(e, tool_name=tool_name)
        except PluginAuthError as e:
            self._statuses[e.plugin_name or ""] = PluginStatus.AUTH_FAILED
            return error_response(e, plugin_name=e.plugin_name or "", tool_name=tool_name)
        except PluginUnavailableError as e:
            return error_response(e, plugin_name=e.plugin_name or "", tool_name=tool_name)
        except PluginError as e:
            return error_response(e, plugin_name=e.plugin_name or "", tool_name=tool_name)

    def get_plugin_metadata(self, name: str) -> PluginMetadata | None:
        return self._health_cache.get(name)

    def get_all_plugin_metadata(self) -> list[PluginMetadata]:
        return list(self._health_cache.values())

    def get_stats(self) -> dict[str, Any]:
        return {
            "total_plugins": self.plugin_count(),
            "total_tools": self.tool_count(),
            "plugins": {
                name: {
                    "status": self._statuses.get(name, PluginStatus.LOADED),
                    "tools": [t.name for t in p.get_tools()],
                }
                for name, p in self._router._plugins.items()
            },
        }
