from __future__ import annotations

from collections.abc import Callable  # noqa: TC003
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request  # noqa: TC002
from starlette.responses import JSONResponse

from app.core.rate_limiter import get_auth_rate_limiter, get_rate_limiter


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Any:
        if request.url.path in ("/health", "/livez", "/readyz", "/"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"

        is_auth = request.url.path.startswith("/api/v1/auth/")
        limiter = get_auth_rate_limiter() if is_auth else get_rate_limiter()

        try:
            if hasattr(limiter, "check"):
                if callable(getattr(limiter, "check", None)):
                    result = limiter.check(key=client_ip)
                    if hasattr(result, "__await__"):
                        await result
        except Exception:
            remaining = limiter.get_remaining(key=client_ip)
            if hasattr(remaining, "__await__"):
                remaining = await remaining
            return JSONResponse(
                status_code=429,
                content={
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "message": f"Rate limit exceeded. {remaining} requests remaining.",
                },
                headers={"X-RateLimit-Remaining": str(remaining)},
            )

        response = await call_next(request)
        remaining = limiter.get_remaining(key=client_ip)
        if hasattr(remaining, "__await__"):
            remaining = await remaining
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
