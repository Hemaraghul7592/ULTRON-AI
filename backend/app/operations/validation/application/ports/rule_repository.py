from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from app.operations.validation.domain.enums import ValidationCategory
    from app.operations.validation.domain.models import ValidationRule


class RuleRepository(Protocol):
    """Abstract repository for validation rule persistence and retrieval."""

    async def get_all_rules(self) -> list[ValidationRule]:
        """Retrieve all validation rules."""
        ...

    async def get_rules_by_category(self, category: ValidationCategory) -> list[ValidationRule]:
        """Retrieve rules filtered by category."""
        ...

    async def get_enabled_rules(self) -> list[ValidationRule]:
        """Retrieve only enabled rules."""
        ...

    async def get_rule_by_code(self, rule_code: str) -> ValidationRule | None:
        """Retrieve a single rule by its code."""
        ...

    async def save_rule(self, rule: ValidationRule) -> None:
        """Persist a validation rule."""
        ...
