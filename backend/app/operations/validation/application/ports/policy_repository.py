from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from app.operations.validation.domain.enums import PolicyType
    from app.operations.validation.domain.models import ValidationPolicy


class PolicyRepository(Protocol):
    """Abstract repository for validation policy persistence and retrieval."""

    async def get_all_policies(self) -> list[ValidationPolicy]:
        """Retrieve all validation policies."""
        ...

    async def get_policies_by_type(self, policy_type: PolicyType) -> list[ValidationPolicy]:
        """Retrieve policies filtered by type."""
        ...

    async def get_active_policies(self) -> list[ValidationPolicy]:
        """Retrieve only active policies."""
        ...

    async def get_policy_by_id(self, policy_id: str) -> ValidationPolicy | None:
        """Retrieve a single policy by its ID."""
        ...

    async def save_policy(self, policy: ValidationPolicy) -> None:
        """Persist a validation policy."""
        ...
