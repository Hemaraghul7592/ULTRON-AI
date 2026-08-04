from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status


class UltronException(Exception):  # noqa: N818
    def __init__(self, message: str, code: str = "ULTRON_ERROR", details: Any = None) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details


class NotFoundException(UltronException):
    def __init__(self, resource: str, identifier: Any) -> None:
        super().__init__(
            message=f"{resource} with identifier '{identifier}' not found",
            code="NOT_FOUND",
            details={"resource": resource, "identifier": str(identifier)},
        )


class DuplicateException(UltronException):
    def __init__(self, resource: str, field: str, value: Any) -> None:
        super().__init__(
            message=f"{resource} with {field}='{value}' already exists",
            code="DUPLICATE",
            details={"resource": resource, "field": field, "value": str(value)},
        )


class ValidationException(UltronException):
    def __init__(self, message: str, details: Any = None) -> None:
        super().__init__(message=message, code="VALIDATION_ERROR", details=details)


class AIServiceException(UltronException):
    def __init__(self, provider: str, message: str, details: Any = None) -> None:
        super().__init__(
            message=f"AI provider '{provider}' error: {message}",
            code="AI_SERVICE_ERROR",
            details={"provider": provider, **(details or {})},
        )


class ProviderUnavailableException(AIServiceException):
    def __init__(self, provider: str, reason: str = "Service unavailable") -> None:
        super().__init__(provider=provider, message=reason)
        self.code = "PROVIDER_UNAVAILABLE"


class ProviderRateLimitException(AIServiceException):
    def __init__(self, provider: str, message: str = "Rate limited") -> None:
        super().__init__(provider=provider, message=message)
        self.code = "PROVIDER_RATE_LIMIT"


class AIAuthenticationException(AIServiceException):
    def __init__(self, provider: str, message: str = "Authentication failed") -> None:
        super().__init__(provider=provider, message=message)
        self.code = "AI_AUTHENTICATION_ERROR"


class AIRateLimitException(AIServiceException):
    def __init__(self, provider: str, message: str = "Rate limited") -> None:
        super().__init__(provider=provider, message=message)
        self.code = "AI_RATE_LIMIT"


class AIContextLengthException(AIServiceException):
    def __init__(self, provider: str, message: str = "Context length exceeded") -> None:
        super().__init__(provider=provider, message=message)
        self.code = "AI_CONTEXT_LENGTH"


class ToolExecutionException(UltronException):
    def __init__(self, tool_name: str, message: str, details: Any = None) -> None:
        super().__init__(
            message=f"Tool '{tool_name}' execution failed: {message}",
            code="TOOL_EXECUTION_ERROR",
            details={"tool": tool_name, **(details or {})},
        )


class RateLimitException(UltronException):
    def __init__(self, limit: int, window: str = "minute") -> None:
        super().__init__(
            message=f"Rate limit exceeded: {limit} requests per {window}",
            code="RATE_LIMIT_EXCEEDED",
            details={"limit": limit, "window": window},
        )


class AuthenticationException(UltronException):
    def __init__(self, message: str = "Authentication required") -> None:
        super().__init__(message=message, code="AUTHENTICATION_ERROR")


class AuthorizationException(UltronException):
    def __init__(self, message: str = "Insufficient permissions") -> None:
        super().__init__(message=message, code="AUTHORIZATION_ERROR")


class PluginException(UltronException):
    def __init__(self, plugin_name: str, message: str) -> None:
        super().__init__(
            message=f"Plugin '{plugin_name}' error: {message}",
            code="PLUGIN_ERROR",
            details={"plugin": plugin_name},
        )


class NotFoundExceptionHTTP(HTTPException):
    def __init__(self, resource: str, identifier: Any) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource} with identifier '{identifier}' not found",
        )


class BadRequestHTTP(HTTPException):
    def __init__(self, detail: str) -> None:
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class ConflictHTTP(HTTPException):
    def __init__(self, detail: str) -> None:
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class UnauthorizedHTTP(HTTPException):
    def __init__(self, detail: str = "Authentication required") -> None:
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class ForbiddenHTTP(HTTPException):
    def __init__(self, detail: str = "Insufficient permissions") -> None:
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)
