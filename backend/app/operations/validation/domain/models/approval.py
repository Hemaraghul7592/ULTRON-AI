from __future__ import annotations

from datetime import datetime  # noqa: TC003
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from app.operations.domain.value_objects import utc_now  # noqa: TC001
from app.operations.validation.domain.enums import (  # noqa: TC001
    ApprovalLevel,
    ApprovalStatus,
)


class ApprovalDecision(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    decision_id: str = Field(default_factory=lambda: str(uuid4()), min_length=1, max_length=100)
    request_id: str = Field(..., min_length=1, max_length=100)
    result_id: str | None = Field(default=None, min_length=1, max_length=100)
    plan_id: str = Field(..., min_length=1, max_length=100)
    decision: ApprovalStatus
    decided_by: str = Field(..., min_length=1, max_length=200)
    reason: str = Field(..., min_length=1, max_length=1000)
    conditions: list[str] = Field(default_factory=list)
    approval_level: ApprovalLevel
    expires_at: datetime
    decided_at: datetime | None = None
    created_at: datetime = Field(default_factory=utc_now)


class ValidationExplanation(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    explanation_id: str = Field(default_factory=lambda: str(uuid4()), min_length=1, max_length=100)
    result_id: str = Field(..., min_length=1, max_length=100)
    summary: str = Field(..., min_length=1, max_length=500)
    detailed_reasons: list[str] = Field(default_factory=list)
    failed_rules_explanation: str = ""
    warning_rules_explanation: str = ""
    confidence_explanation: str = ""
    dependency_explanation: str = ""
    rollback_explanation: str = ""
    suggested_fixes: list[str] = Field(default_factory=list)
    strategy_recommendation: str | None = None
    evidence_summary: str = ""
    created_at: datetime = Field(default_factory=utc_now)


class ValidationSignature(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    signature_id: str = Field(default_factory=lambda: str(uuid4()), min_length=1, max_length=100)
    result_id: str = Field(..., min_length=1, max_length=100)
    plan_id: str = Field(..., min_length=1, max_length=100)
    signature_hash: str = Field(..., min_length=1, max_length=200)
    signed_at: datetime = Field(default_factory=utc_now)
    signed_by: str = Field(..., min_length=1, max_length=200)
    approval_metadata: dict[str, Any] = Field(default_factory=dict)
    verification_method: str = Field(default="sha256", min_length=1, max_length=50)
    expires_at: datetime | None = None
