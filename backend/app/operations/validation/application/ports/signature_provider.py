from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from app.operations.validation.domain.models import ValidationSignature


class SignatureProvider(Protocol):
    """Abstract provider for digital signature operations."""

    async def save_signature(self, signature: ValidationSignature) -> None:
        """Persist a validation signature."""
        ...

    async def get_signature_by_plan(self, plan_id: str) -> ValidationSignature | None:
        """Retrieve the signature for a given plan."""
        ...

    async def get_signature_by_result(self, result_id: str) -> ValidationSignature | None:
        """Retrieve the signature for a given validation result."""
        ...

    async def verify_signature(self, plan_id: str, plan_hash: str) -> bool:
        """Verify that a plan's signature hash is valid."""
        ...
