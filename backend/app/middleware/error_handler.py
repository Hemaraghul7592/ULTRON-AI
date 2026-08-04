from __future__ import annotations

import time
from collections.abc import Callable  # noqa: TC003
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request  # noqa: TC002
from starlette.responses import JSONResponse

from app.core.exceptions import AuthenticationException, UltronException
from app.core.logging import get_logger

logger = get_logger(__name__)


def _error_response(
    status_code: int,
    error_code: str,
    message: str,
    request_id: str | None = None,
    details: Any = None,
) -> JSONResponse:
    body: dict[str, Any] = {
        "error_code": error_code,
        "message": message,
    }
    if request_id:
        body["request_id"] = request_id
    if details:
        body["details"] = details
    return JSONResponse(status_code=status_code, content=body)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Any:
        start = time.monotonic()
        request_id = getattr(request.state, "request_id", None)
        try:
            response = await call_next(request)
            return response
        except AuthenticationException as e:
            logger.warning(
                "authentication_exception",
                code=e.code,
                message=e.message,
                path=request.url.path,
            )
            return _error_response(
                status_code=401,
                error_code=e.code,
                message=e.message,
                request_id=request_id,
                details=e.details,
            )
        except UltronException as e:
            logger.warning(
                "ultron_exception",
                code=e.code,
                message=e.message,
                path=request.url.path,
            )
            return _error_response(
                status_code=400,
                error_code=e.code,
                message=e.message,
                request_id=request_id,
                details=e.details,
            )
        except Exception as e:
            elapsed = (time.monotonic() - start) * 1000
            logger.error(
                "unhandled_exception",
                error=str(e),
                path=request.url.path,
                elapsed_ms=elapsed,
            )
            return _error_response(
                status_code=500,
                error_code="INTERNAL_ERROR",
                message="An internal error occurred",
                request_id=request_id,
            )
