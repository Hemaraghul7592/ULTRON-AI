"""
Strongly-typed DTOs for historical validation data.

These replace the previous ``dict[str, object]`` return types from
``ValidationHistoryRepository`` methods, providing compile-time
type safety and self-documenting schemas.
"""

from __future__ import annotations

from datetime import datetime  # noqa: TC003

from pydantic import BaseModel, ConfigDict, Field

from app.operations.domain.value_objects import utc_now  # noqa: TC001
from app.operations.validation.domain.enums import (  # noqa: TC001
    ValidationDecisionEnum,
    ValidationStatus,
)


class RecurringFailureSummaryDTO(BaseModel):
    """Summary of a rule that fails repeatedly over a period."""

    model_config = ConfigDict(frozen=True)

    rule_code: str = Field(..., min_length=1, max_length=100)
    rule_name: str = Field(..., min_length=1, max_length=200)
    failure_count: int = Field(..., ge=0)
    first_seen: datetime
    last_seen: datetime
    last_failure_reason: str | None = Field(default=None, max_length=2000)


class FailureFrequencyDTO(BaseModel):
    """Frequency data for a single rule over a time period."""

    model_config = ConfigDict(frozen=True)

    rule_code: str = Field(..., min_length=1, max_length=100)
    total_failures: int = Field(..., ge=0)
    failures_per_day: float = Field(..., ge=0.0)
    failure_rate: float = Field(..., ge=0.0, le=1.0)


class HistoricalTrendDTO(BaseModel):
    """A single data point in a historical trend series."""

    model_config = ConfigDict(frozen=True)

    timestamp: datetime
    value: float
    label: str = Field(default="", max_length=200)


class HistoricalPredictionDTO(BaseModel):
    """Predicted validation outcome based on historical patterns."""

    model_config = ConfigDict(frozen=True, use_enum_values=True)

    request_id: str = Field(..., min_length=1, max_length=100)
    predicted_decision: ValidationDecisionEnum = Field(...)
    confidence: float = Field(..., ge=0.0, le=1.0)
    similar_request_ids: list[str] = Field(default_factory=list)
    key_matching_patterns: list[str] = Field(default_factory=list)
    explanation: str | None = Field(default=None, max_length=2000)
    predicted_at: datetime = Field(default_factory=utc_now)


class HistoricalPatternDTO(BaseModel):
    """Historical outcome pattern for similar past requests."""

    model_config = ConfigDict(frozen=True, use_enum_values=True)

    request_id: str = Field(..., min_length=1, max_length=100)
    plan_type: str = Field(..., min_length=1, max_length=100)
    environment: str = Field(..., min_length=1, max_length=100)
    decision: ValidationDecisionEnum = Field(...)
    status: ValidationStatus = Field(...)
    confidence: float = Field(..., ge=0.0, le=1.0)
    recorded_at: datetime
    reason: str = Field(..., min_length=1, max_length=1000)


class HistoricalContextDTO(BaseModel):
    """Historical context aggregated for a given plan pattern."""

    model_config = ConfigDict(frozen=True)

    historical_failures: int = Field(default=0, ge=0)
    false_positive_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    false_negative_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    similar_plan_outcomes: list[HistoricalPatternDTO] = Field(default_factory=list)
