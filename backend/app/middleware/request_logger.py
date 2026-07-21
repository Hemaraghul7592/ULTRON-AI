from __future__ import annotations

import time
from typing import Any, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.logging import get_logger

logger = get_logger(__name__)


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Any:
        start = time.monotonic()
        method = request.method
        path = request.url.path
        request_id = getattr(request.state, "request_id", None)

        response = await call_next(request)

        elapsed_ms = (time.monotonic() - start) * 1000
        status = response.status_code

        logger.info(
            "http_request",
            method=method,
            path=path,
            status=status,
            elapsed_ms=round(elapsed_ms, 2),
            request_id=request_id,
        )

        response.headers["X-Process-Time"] = f"{elapsed_ms:.2f}ms"
        return response