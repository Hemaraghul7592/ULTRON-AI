from __future__ import annotations

from datetime import datetime  # noqa: TC003
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from app.operations.domain.value_objects import utc_now  # noqa: TC001
from app.operations.validation.domain.enums import (  # noqa: TC001
    PluginType,
    PolicyPackType,
    TrendType,
)


class FailingRule(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    rule_code: str = Field(..., min_length=1, max_length=100)
    rule_name: str = Field(..., min_length=1, max_length=200)
    failure_count: int = Field(default=0, ge=0)


class TrendDataPoint(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    timestamp: datetime
    value: float
    label: str = ""


class ValidationHistoryRecord(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    record_id: str = Field(default_factory=lambda: str(uuid4()), min_length=1, max_length=100)
    request_id: str = Field(..., min_length=1, max_length=100)
    result_id: str = Field(..., min_length=1, max_length=100)
    plan_id: str = Field(..., min_length=1, max_length=100)
    incident_id: str | None = Field(default=None, min_length=1, max_length=100)
    decision: str = Field(..., min_length=1, max_length=100)
    risk_score: int = Field(default=0, ge=0, le=100)
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    validation_duration_ms: float = Field(default=0.0, ge=0.0)
    environment: str = Field(..., min_length=1, max_length=100)
    plan_type: str = Field(..., min_length=1, max_length=100)
    rules_triggered: list[str] = Field(default_factory=list)
    was_executed: bool = False
    execution_succeeded: bool | None = None
    is_false_positive: bool = False
    is_false_negative: bool = False
    recorded_at: datetime = Field(default_factory=utc_now)


class ValidationStatistics(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    stat_id: str = Field(default_factory=lambda: str(uuid4()), min_length=1, max_length=100)
    period_start: datetime
    period_end: datetime
    total_validations: int = Field(default=0, ge=0)
    approved_count: int = Field(default=0, ge=0)
    rejected_count: int = Field(default=0, ge=0)
    pending_count: int = Field(default=0, ge=0)
    conditional_count: int = Field(default=0, ge=0)
    average_duration_ms: float = Field(default=0.0, ge=0.0)
    p95_duration_ms: float = Field(default=0.0, ge=0.0)
    p99_duration_ms: float = Field(default=0.0, ge=0.0)
    approval_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    false_positive_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    false_negative_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    top_failing_rules: list[FailingRule] = Field(default_factory=list)
    computed_at: datetime = Field(default_factory=utc_now)


class ValidationTrend(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    trend_id: str = Field(default_factory=lambda: str(uuid4()), min_length=1, max_length=100)
    trend_type: TrendType
    period: str = Field(..., min_length=1, max_length=100)
    data_points: list[TrendDataPoint] = Field(default_factory=list)
    moving_average: float = 0.0
    trend_direction: str = Field(default="stable", min_length=1, max_length=50)
    computed_at: datetime = Field(default_factory=utc_now)


class ValidationCacheEntry(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    cache_key: str = Field(..., min_length=1, max_length=200)
    result_id: str = Field(..., min_length=1, max_length=100)
    plan_id: str = Field(..., min_length=1, max_length=100)
    environment: str = Field(..., min_length=1, max_length=100)
    decision: str = Field(..., min_length=1, max_length=100)
    created_at: datetime
    expires_at: datetime
    hit_count: int = Field(default=0, ge=0)


class PolicyPack(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    pack_id: str = Field(default_factory=lambda: str(uuid4()), min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=1000)
    pack_type: PolicyPackType
    enabled: bool = True
    policy_ids: list[str] = Field(default_factory=list)
    priority: int = Field(default=0, ge=0)
    applicable_environments: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class ValidatorPlugin(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    plugin_id: str = Field(default_factory=lambda: str(uuid4()), min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=1000)
    version: str = Field(..., min_length=1, max_length=50)
    plugin_type: PluginType
    enabled: bool = True
    provides_rules: list[str] = Field(default_factory=list)
    provides_analyzers: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    loaded_at: datetime | None = None
    created_at: datetime = Field(default_factory=utc_now)
