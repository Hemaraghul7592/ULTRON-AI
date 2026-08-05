from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.operations.validation.domain.enums import (  # noqa: TC001
    ValidationDecisionEnum,
    ValidationStatus,
)


class ValidateResponseDTO(BaseModel):
    """DTO for a single validation response."""

    model_config = ConfigDict(frozen=True)

    request_id: str = Field(..., min_length=1, max_length=100)
    plan_id: str = Field(..., min_length=1, max_length=100)
    decision: ValidationDecisionEnum = Field(...)
    status: ValidationStatus = Field(...)
    reason: str | None = Field(default=None, max_length=2000)
    evidence: list[dict[str, object]] = Field(default_factory=list)
    factors: list[dict[str, object]] = Field(default_factory=list)
    validation_time_ms: float | None = Field(default=None, ge=0)
    policy_ids_checked: list[str] = Field(default_factory=list)


class ValidationStatusDTO(BaseModel):
    """DTO for validation status query response."""

    model_config = ConfigDict(frozen=True)

    request_id: str = Field(..., min_length=1, max_length=100)
    plan_id: str = Field(..., min_length=1, max_length=100)
    status: ValidationStatus = Field(...)
    decision: ValidationDecisionEnum | None = Field(default=None)
    reason: str | None = Field(default=None, max_length=2000)
    progress: float = Field(..., ge=0, le=100)


class ValidationExplanationDTO(BaseModel):
    """DTO for a detailed validation explanation."""

    model_config = ConfigDict(frozen=True)

    request_id: str = Field(..., min_length=1, max_length=100)
    plan_id: str = Field(..., min_length=1, max_length=100)
    decision: ValidationDecisionEnum = Field(...)
    summary: str = Field(..., min_length=1, max_length=2000)
    evidence: list[dict[str, object]] = Field(default_factory=list)
    factors: list[dict[str, object]] = Field(default_factory=list)
    policy_ids_checked: list[str] = Field(default_factory=list)


class ValidationSummaryDTO(BaseModel):
    """DTO for a summary of validation results in a batch response."""

    model_config = ConfigDict(frozen=True)

    request_id: str = Field(..., min_length=1, max_length=100)
    plan_id: str = Field(..., min_length=1, max_length=100)
    decision: ValidationDecisionEnum = Field(...)
    status: ValidationStatus = Field(...)


class BatchValidationResponseDTO(BaseModel):
    """DTO for a batch validation response."""

    model_config = ConfigDict(frozen=True)

    batch_id: str = Field(..., min_length=1, max_length=100)
    results: list[ValidateResponseDTO] = Field(...)
    failed_indices: list[int] = Field(default_factory=list)
    total_time_ms: float | None = Field(default=None, ge=0)
    metadata: dict[str, object] = Field(default_factory=dict)
