"""
Request validator for the Validation Engine application layer.

Validates orchestration-level constraints of incoming DTOs that cannot
be expressed through Pydantic field constraints.

DTO field-level validation (required fields, min_length, etc.) is already
enforced by the Pydantic models themselves — this class does **not**
duplicate that work.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.operations.validation.application.dto.requests import (
        BatchValidationRequestDTO,
    )


class ValidationRequestValidator:
    """
    Validates orchestration-level constraints on incoming DTOs.

    Responsibilities:
      - Validate batch request consistency (e.g., conflicting options)
      - Enforce workflow-level constraints
      - Cross-field validation that Pydantic cannot express

    This class does **not** re-validate fields already covered by
    Pydantic ``Field`` constraints on the DTOs themselves.
    Business-rule validation belongs to downstream engines (Milestone 2C+).
    """

    @staticmethod
    def validate_batch(request: BatchValidationRequestDTO) -> None:
        """
        Validate orchestration-level constraints on a batch request.

        Args:
            request: The batch validation request DTO to check.

        Raises:
            ValueError: If an orchestration-level constraint is violated.
        """
        if len(request.requests) > 1000:
            raise ValueError("Batch size exceeds maximum of 1000 requests.")
