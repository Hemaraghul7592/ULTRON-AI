"""
Mapper for converting between application DTOs and domain models.

This component is the **only** place where DTO-to-domain and
domain-to-DTO conversions happen.  ValidationService delegates all
mapping to this class so it remains a pure orchestrator.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.operations.validation.application.dto.responses import (
    ValidateResponseDTO,
)
from app.operations.validation.domain.enums import ValidationStatus
from app.operations.validation.domain.models.request import (
    ValidationDecision,
    ValidationRequest,
)

if TYPE_CHECKING:
    from app.operations.validation.application.dto.requests import (
        ValidateRequestDTO,
    )


class ValidationMapper:
    """
    Bidirectional mapper between application DTOs and domain models.

    - ``to_domain()`` converts an incoming request DTO to a domain
      ``ValidationRequest``.  The domain model auto-generates ``request_id``
      via its ``default_factory``, so the mapper does not need to
      generate IDs.
    - ``to_response()`` converts a domain ``ValidationDecision`` back
      into a response DTO for the application boundary.
    """

    @staticmethod
    def to_domain(request: ValidateRequestDTO) -> ValidationRequest:
        """
        Convert a ValidateRequestDTO to the domain ValidationRequest.

        The domain model auto-generates ``request_id`` through its
        ``default_factory`` — this mapper does not generate IDs.
        """
        return ValidationRequest(
            plan_id=request.plan_id,
            incident_id=request.incident_id,
            plan_json=dict(request.metadata),
            plan_type=request.plan_type,
            environment=request.environment,
            requested_by=request.requested_by,
            priority=request.priority,
            timeout_seconds=request.timeout_seconds,
            metadata=dict(request.metadata),
        )

    @staticmethod
    def to_response(
        decision: ValidationDecision,
        request: ValidationRequest,
    ) -> ValidateResponseDTO:
        """
        Convert a domain ValidationDecision to a ValidateResponseDTO.
        """
        return ValidateResponseDTO(
            request_id=request.request_id,
            plan_id=request.plan_id,
            decision=decision.decision,
            status=ValidationStatus.COMPLETED,
            reason=decision.decision_reason,
            evidence=[],
            factors=[],
            validation_time_ms=decision.validation_duration_ms,
            policy_ids_checked=decision.failed_rules + decision.warning_rules,
        )
