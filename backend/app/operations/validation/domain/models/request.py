from __future__ import annotations

from datetime import datetime  # noqa: TC003
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from app.operations.domain.value_objects import utc_now  # noqa: TC001
from app.operations.validation.domain.enums import (  # noqa: TC001
    PolicyEnforcement,
    PolicyType,
    ValidationCategory,
    ValidationDecisionEnum,
    ValidationSeverity,
)
from app.operations.validation.domain.value_objects import ConfidenceScore  # noqa: TC001


class ValidationRequest(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    request_id: str = Field(default_factory=lambda: str(uuid4()), min_length=1, max_length=100)
    plan_id: str = Field(..., min_length=1, max_length=100)
    incident_id: str | None = Field(default=None, min_length=1, max_length=100)
    plan_json: dict[str, Any] = Field(default_factory=dict)
    plan_type: str = Field(default="infrastructure_repair", min_length=1, max_length=100)
    environment: str = Field(..., min_length=1, max_length=100)
    requested_by: str = Field(..., min_length=1, max_length=200)
    requested_at: datetime = Field(default_factory=utc_now)
    priority: int = Field(default=0, ge=0, le=100)
    timeout_seconds: int = Field(default=300, ge=1, le=3600)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ValidationDecision(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    decision: ValidationDecisionEnum
    decision_reason: str = Field(..., min_length=1, max_length=1000)
    decided_at: datetime = Field(default_factory=utc_now)
    decided_by: str = Field(..., min_length=1, max_length=200)
    conditions: list[str] = Field(default_factory=list)
    expiration_at: datetime | None = None
    validation_duration_ms: float = Field(default=0.0, ge=0.0)
    detailed_reasons: list[str] = Field(default_factory=list)
    failed_rules: list[str] = Field(default_factory=list)
    warning_rules: list[str] = Field(default_factory=list)
    confidence_explanation: str = ""
    suggested_fixes: list[str] = Field(default_factory=list)
    strategy_recommendation: str | None = None
    dependency_explanation: str = ""
    rollback_explanation: str = ""
    evidence_summary: str = ""


class ValidationRule(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    rule_id: str = Field(default_factory=lambda: str(uuid4()), min_length=1, max_length=100)
    rule_code: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=1000)
    category: ValidationCategory
    severity: ValidationSeverity
    enabled: bool = True
    conditions: list[dict[str, Any]] = Field(default_factory=list)
    message_on_pass: str = ""
    message_on_fail: str = ""
    suggested_fix: str = ""
    plugin_id: str | None = Field(default=None, min_length=1, max_length=100)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class ValidationPolicy(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    policy_id: str = Field(default_factory=lambda: str(uuid4()), min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=1000)
    policy_type: PolicyType
    enforcement: PolicyEnforcement
    enabled: bool = True
    conditions: list[dict[str, Any]] = Field(default_factory=list)
    applicable_environments: list[str] = Field(default_factory=list)
    policy_pack_id: str | None = Field(default=None, min_length=1, max_length=100)
    message_on_pass: str = ""
    message_on_fail: str = ""
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class ValidationEvidence(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    evidence_id: str = Field(default_factory=lambda: str(uuid4()), min_length=1, max_length=100)
    result_id: str = Field(..., min_length=1, max_length=100)
    evidence_type: str = Field(..., min_length=1, max_length=100)
    source: str = Field(..., min_length=1, max_length=200)
    key: str = Field(..., min_length=1, max_length=200)
    value: Any
    confidence: ConfidenceScore
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class ValidationFailure(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    failure_id: str = Field(default_factory=lambda: str(uuid4()), min_length=1, max_length=100)
    result_id: str = Field(..., min_length=1, max_length=100)
    rule_id: str = Field(..., min_length=1, max_length=100)
    rule_code: str = Field(..., min_length=1, max_length=100)
    rule_name: str = Field(..., min_length=1, max_length=200)
    category: ValidationCategory
    severity: ValidationSeverity
    reason: str = Field(..., min_length=1, max_length=1000)
    suggested_fix: str = ""
    created_at: datetime = Field(default_factory=utc_now)


class ValidationWarning(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    warning_id: str = Field(default_factory=lambda: str(uuid4()), min_length=1, max_length=100)
    result_id: str = Field(..., min_length=1, max_length=100)
    rule_id: str = Field(..., min_length=1, max_length=100)
    rule_code: str = Field(..., min_length=1, max_length=100)
    rule_name: str = Field(..., min_length=1, max_length=200)
    category: ValidationCategory
    severity: ValidationSeverity
    message: str = Field(..., min_length=1, max_length=1000)
    created_at: datetime = Field(default_factory=utc_now)
