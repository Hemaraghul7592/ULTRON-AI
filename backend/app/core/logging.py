from __future__ import annotations

import logging
import re
import sys
from collections.abc import Mapping
from typing import Any

import structlog

from app.core.config import get_settings

SENSITIVE_KEYS = {
    "password",
    "passwd",
    "secret",
    "token",
    "api_key",
    "authorization",
    "auth",
    "jwt",
    "access_token",
    "refresh_token",
    "private_key",
    "secret_key",
    "encryption_key",
    "credentials",
    "prompt",
    "content",
    "conversation",
    "email",
    "username",
    "user_id",
    "query",
    "error",
    "detail",
    "traceback",
}

_BEARER_PATTERN = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]+")
_SECRET_PATTERN = re.compile(
    r"(?i)\b(api[_-]?key|access[_-]?token|refresh[_-]?token|secret|password)\s*[:=]\s*[^\s,;]+",
)


def _sanitize_value(key: str, value: Any) -> Any:
    normalized = key.lower().replace("-", "_").replace(" ", "_")
    if normalized in SENSITIVE_KEYS:
        return "***REDACTED***"
    if isinstance(value, Mapping):
        return {str(k): _sanitize_value(str(k), v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [_sanitize_value(key, item) for item in value]
    if isinstance(value, str):
        value = _BEARER_PATTERN.sub("Bearer ***REDACTED***", value)
        value = _SECRET_PATTERN.sub(lambda match: f"{match.group(1)}=***REDACTED***", value)
        if len(value) > 500:
            value = value[:500] + "...[truncated]"
    return value


def sanitize_event_dict(logger: logging.Logger, method_name: str, event_dict: dict) -> dict:
    return {str(key): _sanitize_value(str(key), value) for key, value in event_dict.items()}


def setup_logging() -> None:
    settings = get_settings()

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        sanitize_event_dict,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.CallsiteParameterAdder(
            [
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.FUNC_NAME,
                structlog.processors.CallsiteParameter.LINENO,
            ],
        ),
    ]

    if settings.DEBUG:
        renderer: structlog.types.Processor = structlog.dev.ConsoleRenderer()
    else:
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.processors.format_exc_info,
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(settings.LOG_LEVEL),
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stderr,
        level=logging.getLevelName(settings.LOG_LEVEL),
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
