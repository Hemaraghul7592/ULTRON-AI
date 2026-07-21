from __future__ import annotations

import abc
import time
from typing import Any, TypedDict

from app.tools.base import BasePlugin, BaseTool


class PluginHealth(TypedDict, total=False):
    status: str
    message: str
    last_check: float
    details: dict[str, Any]


class PermissionScope(TypedDict, total=False):
    name: str
    description: str
    required_credentials: list[str]
    actions: list[str]


class PluginMetadata(TypedDict, total=False):
    name: str
    version: str
    description: str
    author: str
    homepage: str
    license: str
    tags: list[str]


class PluginStatus:
    LOADED = "loaded"
    INITIALIZED = "initialized"
    AVAILABLE = "available"
    DISABLED = "disabled"
    AUTH_FAILED = "auth_failed"
    RATE_LIMITED = "rate_limited"
    UNAVAILABLE = "unavailable"
    ERROR = "error"

    _LABELS = {
        LOADED: "Loaded",
        INITIALIZED: "Initialized",
        AVAILABLE: "Available",
        DISABLED: "Disabled",
        AUTH_FAILED: "Auth Failed",
        RATE_LIMITED: "Rate Limited",
        UNAVAILABLE: "Unavailable",
        ERROR: "Error",
    }

    @classmethod
    def label(cls, status: str) -> str:
        return cls._LABELS.get(status, status)


class PluginInterface(BasePlugin):
    @property
    @abc.abstractmethod
    def required_credentials(self) -> list[str]:
        pass

    def get_metadata(self) -> PluginMetadata:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
        }

    def get_permission_scope(self) -> PermissionScope:
        return {
            "name": self.name,
            "description": self.description,
            "required_credentials": self.required_credentials,
            "actions": [t.name for t in self.get_tools()],
        }

    async def health_check(self) -> PluginHealth:
        return {
            "status": PluginStatus.AVAILABLE,
            "message": "",
            "last_check": time.time(),
        }

    async def validate(self) -> bool:
        return True

    def get_status(self) -> str:
        return PluginStatus.AVAILABLE

    async def execute_tool(self, tool_name: str, **kwargs: Any) -> str:
        for tool in self.get_tools():
            if tool.name == tool_name:
                return await tool.execute(**kwargs)
        raise ValueError(f"Tool '{tool_name}' not found in plugin '{self.name}'")
