from __future__ import annotations

import logging
import sys

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
}


def sanitize_event_dict(logger: logging.Logger, method_name: str, event_dict: dict) -> dict:
    for key in list(event_dict.keys()):
        lower_key = key.lower().replace("-", "_").replace(" ", "_")
        if lower_key in SENSITIVE_KEYS:
            event_dict[key] = "***REDACTED***"
        elif isinstance(event_dict[key], str) and len(event_dict[key]) > 500:
            event_dict[key] = event_dict[key][:500] + "...[truncated]"
    return event_dict


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
