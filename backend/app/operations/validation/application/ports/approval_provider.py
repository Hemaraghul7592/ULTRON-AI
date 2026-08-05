from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from app.operations.validation.domain.enums import ApprovalLevel
    from app.operations.validation.domain.models import ApprovalDecision


class ApprovalProvider(Protocol):
    """Abstract provider for approval workflow operations."""

    async def check_approval_status(
        self,
        request_id: str,
        required_level: ApprovalLevel,
    ) -> ApprovalDecision | None:
        """Check if a required approval level has been satisfied."""
        ...

    async def get_pending_approvals(
        self,
        *,
        approval_level: ApprovalLevel | None = None,
        limit: int = 50,
    ) -> list[ApprovalDecision]:
        """Retrieve pending approval decisions."""
        ...

    async def save_approval(self, approval: ApprovalDecision) -> None:
        """Persist an approval decision."""
        ...
