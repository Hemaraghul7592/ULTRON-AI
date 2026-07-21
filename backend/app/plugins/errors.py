from __future__ import annotations

from typing import Any


class PluginError(Exception):
    def __init__(
        self,
        message: str = "",
        plugin_name: str = "",
        original_error: Exception | None = None,
    ) -> None:
        self.plugin_name = plugin_name
        self.original_error = original_error
        super().__init__(message)


class PluginNotFoundError(PluginError):
    pass


class PluginAuthError(PluginError):
    pass


class PluginRateLimitError(PluginError):
    pass


class PluginTimeoutError(PluginError):
    pass


class PluginExecutionError(PluginError):
    pass


class PluginUnavailableError(PluginError):
    pass


class PluginConfigError(PluginError):
    pass


ERROR_MAP: dict[str, type[PluginError]] = {
    "auth_failed": PluginAuthError,
    "rate_limited": PluginRateLimitError,
    "timeout": PluginTimeoutError,
    "unavailable": PluginUnavailableError,
    "execution_error": PluginExecutionError,
    "config_error": PluginConfigError,
}


def normalize_error(
    error: Exception,
    plugin_name: str = "",
) -> PluginError:
    if isinstance(error, PluginError):
        return error

    msg = str(error)

    if "401" in msg or "403" in msg or "unauthorized" in msg.lower() or "auth" in msg.lower():
        return PluginAuthError(message=msg, plugin_name=plugin_name, original_error=error)
    if "429" in msg or "rate" in msg.lower():
        return PluginRateLimitError(message=msg, plugin_name=plugin_name, original_error=error)
    if "timeout" in msg.lower():
        return PluginTimeoutError(message=msg, plugin_name=plugin_name, original_error=error)
    if "5" in msg and ("not found" in msg.lower() or "unavailable" in msg.lower()):
        pass

    return PluginExecutionError(message=msg, plugin_name=plugin_name, original_error=error)


def error_response(
    error: Exception,
    plugin_name: str = "",
    tool_name: str = "",
) -> dict[str, Any]:
    normalized = normalize_error(error, plugin_name)
    error_type = type(normalized).__name__
    return {
        "success": False,
        "error": str(normalized),
        "error_type": error_type,
        "plugin": plugin_name,
        "tool": tool_name,
    }


def success_response(
    result: str,
    tool_name: str = "",
    plugin_name: str = "",
) -> dict[str, Any]:
    return {
        "success": True,
        "result": result,
        "plugin": plugin_name,
        "tool": tool_name,
    }
