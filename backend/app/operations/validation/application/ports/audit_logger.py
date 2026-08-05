from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from app.operations.validation.domain.models import (
        ValidationDecision,
        ValidationRequest,
    )


class AuditLogger(Protocol):
    """Abstract provider for audit trail logging."""

    async def log_validation_request(self, request: ValidationRequest) -> None:
        """Log a validation request for audit purposes."""
        ...

    async def log_validation_result(
        self,
        request: ValidationRequest,
        decision: ValidationDecision,
    ) -> None:
        """Log a validation result for audit purposes."""
        ...

    async def log_approval_action(
        self,
        request_id: str,
        actor: str,
        action: str,
        reason: str,
    ) -> None:
        """Log an approval workflow action."""
        ...

    async def log_cancel_action(
        self,
        request_id: str,
        actor: str,
        reason: str,
    ) -> None:
        """Log a cancellation action."""
        ...
