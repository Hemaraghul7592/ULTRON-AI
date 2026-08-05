from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.operations.validation.application.dto.requests import (
        BatchValidationRequestDTO,
        ExplainRequestDTO,
        ValidateRequestDTO,
        ValidationStatusRequestDTO,
    )
    from app.operations.validation.application.dto.responses import (
        BatchValidationResponseDTO,
        ValidateResponseDTO,
        ValidationExplanationDTO,
        ValidationStatusDTO,
    )
    from app.operations.validation.application.ports.approval_provider import (
        ApprovalProvider,
    )
    from app.operations.validation.application.ports.audit_logger import (
        AuditLogger,
    )
    from app.operations.validation.application.ports.cache_provider import (
        CacheProvider,
    )
    from app.operations.validation.application.ports.policy_repository import (
        PolicyRepository,
    )
    from app.operations.validation.application.ports.rule_repository import (
        RuleRepository,
    )
    from app.operations.validation.application.ports.signature_provider import (
        SignatureProvider,
    )
    from app.operations.validation.application.ports.validation_history_repository import (
        ValidationHistoryRepository,
    )
    from app.operations.validation.application.services.validation_mapper import (
        ValidationMapper,
    )
    from app.operations.validation.application.services.validation_request_validator import (
        ValidationRequestValidator,
    )

_DOWNSTREAM_ENGINES = (
    "RuleEngine, PolicyEngine, ApprovalEngine, DecisionEngine and SimulationEngine"
)
_MILESTONE_2C = "Implemented in Milestone 2C."


class ValidationService:
    """
    Pure orchestrator for the validation pipeline.

    The ValidationService coordinates the execution of the validation
    pipeline.  It does **not** validate DTO fields, map objects,
    generate IDs, or make decisions — those responsibilities live in
    dedicated components.

    Orchestration flow:

        Single request:
          Request DTO
          → ValidationMapper.to_domain()
          → AuditLogger.log_validation_request()
          → CacheProvider.get()
          → [Cache miss] RuleEngine → PolicyEngine → ApprovalEngine
          → DecisionEngine → SimulationEngine  (Milestone 2C+)
          → ValidationHistoryRepository
          → ValidationMapper.to_response()
          → Response DTO

        Batch request:
          Batch DTO
          → ValidationRequestValidator.validate_batch()
          → Delegate each item to pipeline (Milestone 2C+)
          → Aggregate into response DTO

    Dependencies:
      - ValidationRequestValidator — orchestration-level validation
      - ValidationMapper — DTO↔Domain conversion
      - AuditLogger — audit trail
      - CacheProvider — result caching
      - RuleRepository — rule definitions (future RuleEngine)
      - PolicyRepository — policy definitions (future PolicyEngine)
      - ApprovalProvider — approval workflow (future ApprovalEngine)
      - ValidationHistoryRepository — historical data
      - SignatureProvider — digital signatures
    """

    def __init__(
        self,
        *,
        rule_repository: RuleRepository,
        policy_repository: PolicyRepository,
        history_repository: ValidationHistoryRepository,
        approval_provider: ApprovalProvider,
        cache_provider: CacheProvider,
        audit_logger: AuditLogger,
        signature_provider: SignatureProvider,
        request_validator: ValidationRequestValidator,
        mapper: ValidationMapper,
    ) -> None:
        self._rule_repository = rule_repository
        self._policy_repository = policy_repository
        self._history_repository = history_repository
        self._approval_provider = approval_provider
        self._cache_provider = cache_provider
        self._audit_logger = audit_logger
        self._signature_provider = signature_provider
        self._validator = request_validator
        self._mapper = mapper

    async def validate(self, request: ValidateRequestDTO) -> ValidateResponseDTO:
        """
        Orchestrate the validation pipeline for a single request.

        Flow:
          1. Mapper.to_domain()         — DTO → domain request
          2. AuditLogger.log_validation_request()
          3. CacheProvider.get()       — cache check
          4. [hit] AuditLogger.log_validation_result() → Mapper.to_response()
          5. [miss] Delegate to downstream engines (Milestone 2C+)

        Raises:
            NotImplementedError: When a downstream engine is not yet implemented.
        """
        domain_request = self._mapper.to_domain(request)
        await self._audit_logger.log_validation_request(domain_request)

        cached = await self._cache_provider.get(domain_request)
        if cached is not None:
            await self._audit_logger.log_validation_result(domain_request, cached)
            return self._mapper.to_response(cached, domain_request)

        raise NotImplementedError(
            f"Orchestration pipeline requires {_DOWNSTREAM_ENGINES}, {_MILESTONE_2C}"
        )

    async def validate_async(
        self,
        request: ValidateRequestDTO,
    ) -> str:
        """
        Start an asynchronous validation and emit a request ID for polling.

        Flow:
          1. Mapper.to_domain()
          2. AuditLogger.log_validation_request()
          3. Delegate to downstream engines (Milestone 2C+)

        Returns:
            A ``request_id`` string for use with ``get_validation_status()``.

        Raises:
            NotImplementedError: When a downstream engine is not yet implemented.
        """
        domain_request = self._mapper.to_domain(request)
        await self._audit_logger.log_validation_request(domain_request)

        raise NotImplementedError(
            f"Asynchronous validation requires {_DOWNSTREAM_ENGINES}, {_MILESTONE_2C}"
        )

    async def get_validation_status(
        self,
        request_dto: ValidationStatusRequestDTO,
    ) -> ValidationStatusDTO:
        """
        Query the status of a previously submitted validation request.

        Delegates to the history repository to look up the current
        status and (if available) the final decision.

        Raises:
            NotImplementedError: When the status-tracking layer
                (Milestone 2C) is not yet available.
        """
        raise NotImplementedError(
            f"Status tracking requires a ValidationRepository, {_MILESTONE_2C}"
        )

    async def explain_validation(
        self,
        request_dto: ExplainRequestDTO,
    ) -> ValidationExplanationDTO:
        """
        Generate a detailed explanation for a completed validation.

        Delegates to the ExplainabilityService (Milestone 2C+) to
        assemble evidence, factors, and policy details.

        Raises:
            NotImplementedError: When the explainability service
                (Milestone 2C) is not yet available.
        """
        raise NotImplementedError(
            f"Explainability requires the ExplainabilityService, {_MILESTONE_2C}"
        )

    async def cancel_validation(
        self,
        request_id: str,
        actor: str,
        reason: str,
    ) -> bool:
        """
        Cancel an in-progress validation.

        Emits an audit-log entry for the cancellation request.
        Returns ``True`` only when the future execution layer
        confirms the cancellation.

        Args:
            request_id: The request ID of the validation to cancel.
            actor: The user/service requesting cancellation.
            reason: Human-readable reason for cancellation.

        Returns:
            ``True`` if cancelled, ``False`` otherwise.

        Raises:
            NotImplementedError: When the async execution layer
                (Milestone 2C) is not yet available.
        """
        await self._audit_logger.log_cancel_action(
            request_id=request_id,
            actor=actor,
            reason=reason,
        )

        raise NotImplementedError(
            f"Cancellation tracking requires the async execution layer, {_MILESTONE_2C}"
        )

    async def validate_batch(
        self,
        request: BatchValidationRequestDTO,
    ) -> BatchValidationResponseDTO:
        """
        Orchestrate validation for multiple requests in a single batch.

        Flow:
          1. Validator.validate_batch()    — orchestration-level validation
          2. Delegate each item to the pipeline (Milestone 2C+)
          3. Aggregate results into a single response DTO

        Raises:
            ValueError: If an orchestration-level constraint is violated.
            NotImplementedError: When a downstream engine is not yet
                implemented.
        """
        self._validator.validate_batch(request)

        raise NotImplementedError(
            f"Batch orchestration requires {_DOWNSTREAM_ENGINES}, {_MILESTONE_2C}"
        )
