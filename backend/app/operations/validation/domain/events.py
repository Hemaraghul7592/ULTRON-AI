from __future__ import annotations

from datetime import datetime  # noqa: TC003
from typing import Any
from uuid import uuid4

from pydantic import Field

from app.operations.domain.value_objects import DomainModel, utc_now  # noqa: TC001


class ValidationDomainEvent(DomainModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str
    occurred_at: datetime = Field(default_factory=utc_now)
    correlation_id: str | None = None
    source: str = Field(default="uaes-validation", min_length=1, max_length=100)

    def payload(self) -> dict[str, Any]:
        return self.to_dict()


class ValidationRequested(ValidationDomainEvent):
    event_type: str = "validation.requested"
    request_id: str = Field(..., min_length=1, max_length=100)
    plan_id: str = Field(..., min_length=1, max_length=100)
    incident_id: str | None = Field(default=None, min_length=1, max_length=100)
    environment: str = Field(..., min_length=1, max_length=100)
    requested_by: str = Field(..., min_length=1, max_length=200)


class ValidationStarted(ValidationDomainEvent):
    event_type: str = "validation.started"
    request_id: str = Field(..., min_length=1, max_length=100)
    plan_id: str = Field(..., min_length=1, max_length=100)


class ValidationCompleted(ValidationDomainEvent):
    event_type: str = "validation.completed"
    request_id: str = Field(..., min_length=1, max_length=100)
    result_id: str = Field(..., min_length=1, max_length=100)
    plan_id: str = Field(..., min_length=1, max_length=100)
    decision: str = Field(..., min_length=1, max_length=100)
    validation_duration_ms: float = Field(default=0.0, ge=0.0)


class ValidationFailed(ValidationDomainEvent):
    event_type: str = "validation.failed"
    request_id: str = Field(..., min_length=1, max_length=100)
    error: str = Field(..., min_length=1, max_length=1000)
    stack_trace: str = ""


class ValidationRuleTriggered(ValidationDomainEvent):
    event_type: str = "validation.rule_triggered"
    request_id: str = Field(..., min_length=1, max_length=100)
    result_id: str = Field(..., min_length=1, max_length=100)
    rule_code: str = Field(..., min_length=1, max_length=100)
    rule_name: str = Field(..., min_length=1, max_length=200)
    result: str = Field(..., min_length=1, max_length=20)


class ValidationBlockerDetected(ValidationDomainEvent):
    event_type: str = "validation.blocker_detected"
    request_id: str = Field(..., min_length=1, max_length=100)
    result_id: str = Field(..., min_length=1, max_length=100)
    failure_id: str = Field(..., min_length=1, max_length=100)
    rule_code: str = Field(default="", min_length=1, max_length=100)
    rule_name: str = Field(..., min_length=1, max_length=200)
    reason: str = Field(..., min_length=1, max_length=1000)


class ValidationWarningGenerated(ValidationDomainEvent):
    event_type: str = "validation.warning_generated"
    request_id: str = Field(..., min_length=1, max_length=100)
    result_id: str = Field(..., min_length=1, max_length=100)
    warning_id: str = Field(..., min_length=1, max_length=100)
    rule_code: str = Field(..., min_length=1, max_length=100)
    rule_name: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=1000)


class ValidationApprovalRequired(ValidationDomainEvent):
    event_type: str = "validation.approval_required"
    request_id: str = Field(..., min_length=1, max_length=100)
    plan_id: str = Field(..., min_length=1, max_length=100)
    approval_level: str = Field(..., min_length=1, max_length=100)
    risk_score: int = Field(default=0, ge=0, le=100)


class ValidationApprovalGranted(ValidationDomainEvent):
    event_type: str = "validation.approval_granted"
    request_id: str = Field(..., min_length=1, max_length=100)
    decided_by: str = Field(..., min_length=1, max_length=200)
    conditions: list[str] = Field(default_factory=list)


class ValidationApprovalRejected(ValidationDomainEvent):
    event_type: str = "validation.approval_rejected"
    request_id: str = Field(..., min_length=1, max_length=100)
    decided_by: str = Field(..., min_length=1, max_length=200)
    reason: str = Field(..., min_length=1, max_length=1000)


class ValidationApprovalEscalated(ValidationDomainEvent):
    event_type: str = "validation.approval_escalated"
    request_id: str = Field(..., min_length=1, max_length=100)
    from_level: str = Field(..., min_length=1, max_length=100)
    to_level: str = Field(..., min_length=1, max_length=100)


class ValidationPermissionGranted(ValidationDomainEvent):
    event_type: str = "validation.permission_granted"
    plan_id: str = Field(..., min_length=1, max_length=100)
    permission_id: str = Field(..., min_length=1, max_length=100)
    result_id: str = Field(..., min_length=1, max_length=100)
    granted_by: str = Field(..., min_length=1, max_length=200)
    expires_at: datetime = Field(default_factory=utc_now)
    conditions: list[str] = Field(default_factory=list)


class ValidationPermissionRevoked(ValidationDomainEvent):
    event_type: str = "validation.permission_revoked"
    plan_id: str = Field(..., min_length=1, max_length=100)
    permission_id: str = Field(..., min_length=1, max_length=100)
    reason: str = Field(..., min_length=1, max_length=1000)


class ValidationExpired(ValidationDomainEvent):
    event_type: str = "validation.expired"
    request_id: str = Field(..., min_length=1, max_length=100)
    plan_id: str = Field(..., min_length=1, max_length=100)


class ValidationSignatureCreated(ValidationDomainEvent):
    event_type: str = "validation.signature_created"
    plan_id: str = Field(..., min_length=1, max_length=100)
    signature_id: str = Field(..., min_length=1, max_length=100)
    signature_hash: str = Field(..., min_length=1, max_length=200)


class ValidationSignatureVerified(ValidationDomainEvent):
    event_type: str = "validation.signature_verified"
    plan_id: str = Field(..., min_length=1, max_length=100)
    signature_id: str = Field(..., min_length=1, max_length=100)
    valid: bool = False


class ValidationHistoryRecorded(ValidationDomainEvent):
    event_type: str = "validation.history_recorded"
    record_id: str = Field(..., min_length=1, max_length=100)
    plan_id: str = Field(..., min_length=1, max_length=100)
    decision: str = Field(..., min_length=1, max_length=100)


class ValidationTrendComputed(ValidationDomainEvent):
    event_type: str = "validation.trend_computed"
    trend_id: str = Field(..., min_length=1, max_length=100)
    trend_type: str = Field(..., min_length=1, max_length=100)
    period: str = Field(..., min_length=1, max_length=100)


class ValidationCacheHit(ValidationDomainEvent):
    event_type: str = "validation.cache_hit"
    plan_id: str = Field(..., min_length=1, max_length=100)
    cache_key: str = Field(..., min_length=1, max_length=200)


class ValidationCacheMiss(ValidationDomainEvent):
    event_type: str = "validation.cache_miss"
    plan_id: str = Field(..., min_length=1, max_length=100)
    cache_key: str = Field(..., min_length=1, max_length=200)


class ValidationMetricsRecorded(ValidationDomainEvent):
    event_type: str = "validation.metrics_recorded"
    request_id: str = Field(..., min_length=1, max_length=100)
    duration_ms: float = Field(default=0.0, ge=0.0)
    decision: str = Field(..., min_length=1, max_length=100)


def validation_event_from_dict(data: dict[str, Any]) -> ValidationDomainEvent:
    event_type = data.get("event_type", "")
    event_map: dict[str, type[ValidationDomainEvent]] = {
        "validation.requested": ValidationRequested,
        "validation.started": ValidationStarted,
        "validation.completed": ValidationCompleted,
        "validation.failed": ValidationFailed,
        "validation.rule_triggered": ValidationRuleTriggered,
        "validation.blocker_detected": ValidationBlockerDetected,
        "validation.warning_generated": ValidationWarningGenerated,
        "validation.approval_required": ValidationApprovalRequired,
        "validation.approval_granted": ValidationApprovalGranted,
        "validation.approval_rejected": ValidationApprovalRejected,
        "validation.approval_escalated": ValidationApprovalEscalated,
        "validation.permission_granted": ValidationPermissionGranted,
        "validation.permission_revoked": ValidationPermissionRevoked,
        "validation.expired": ValidationExpired,
        "validation.signature_created": ValidationSignatureCreated,
        "validation.signature_verified": ValidationSignatureVerified,
        "validation.history_recorded": ValidationHistoryRecorded,
        "validation.trend_computed": ValidationTrendComputed,
        "validation.cache_hit": ValidationCacheHit,
        "validation.cache_miss": ValidationCacheMiss,
        "validation.metrics_recorded": ValidationMetricsRecorded,
    }
    event_cls = event_map.get(event_type)
    if event_cls is None:
        return ValidationDomainEvent.model_validate(data)
    return event_cls.model_validate(data)
