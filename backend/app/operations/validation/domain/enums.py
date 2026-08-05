from __future__ import annotations

from enum import StrEnum


class ValidationStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMED_OUT = "timed_out"


class ValidationDecisionEnum(StrEnum):
    APPROVED = "approved"
    REJECTED = "rejected"
    CONDITIONAL = "conditional"
    PENDING_APPROVAL = "pending_approval"
    NEEDS_REVIEW = "needs_review"
    DEFERRED = "deferred"
    TIMED_OUT = "timed_out"
    ESCALATED = "escalated"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class ValidationSeverity(StrEnum):
    BLOCKER = "blocker"
    WARNING = "warning"
    INFO = "info"


class ValidationCategory(StrEnum):
    SAFETY = "safety"
    DEPENDENCY = "dependency"
    COMPATIBILITY = "compatibility"
    RESOURCE = "resource"
    POLICY = "policy"
    SECURITY = "security"
    ROLLBACK = "rollback"
    COST = "cost"


class ApprovalLevel(StrEnum):
    AUTO = "auto"
    DEVELOPER = "developer"
    MAINTAINER = "maintainer"
    OPERATIONS = "operations"
    ADMINISTRATOR = "administrator"
    EMERGENCY = "emergency"


class ApprovalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVIEW = "needs_review"
    DEFERRED = "deferred"
    TIMED_OUT = "timed_out"
    ESCALATED = "escalated"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class ExecutionPermissionStatus(StrEnum):
    GRANTED = "granted"
    DENIED = "denied"
    EXPIRED = "expired"
    REVOKED = "revoked"


class CascadeRisk(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RollbackComplexity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    IMPOSSIBLE = "impossible"


class PolicyEnforcement(StrEnum):
    HARD = "hard"
    SOFT = "soft"


class PolicyType(StrEnum):
    APPROVAL = "approval"
    COST = "cost"
    MAINTENANCE = "maintenance"
    PRODUCTION = "production"
    SECURITY = "security"
    BUSINESS = "business"


class BlockerType(StrEnum):
    RULE_VIOLATION = "rule_violation"
    POLICY_VIOLATION = "policy_violation"
    APPROVAL_REQUIRED = "approval_required"
    SAFETY = "safety"
    RESOURCE = "resource"
    SECURITY = "security"


class PolicyPackType(StrEnum):
    PRODUCTION = "production"
    DEVELOPMENT = "development"
    TESTING = "testing"
    INFRASTRUCTURE = "infrastructure"
    FINANCIAL = "financial"
    PERSONAL_ASSISTANT = "personal_assistant"
    EXPERIMENTAL = "experimental"
    CUSTOM = "custom"


class PluginType(StrEnum):
    INFRASTRUCTURE = "infrastructure"
    CLOUD = "cloud"
    DATABASE = "database"
    FINANCIAL = "financial"
    CALENDAR = "calendar"
    COMMUNICATION = "communication"
    CUSTOM = "custom"


class TrendType(StrEnum):
    RISK = "risk"
    CONFIDENCE = "confidence"
    FAILURE = "failure"
    APPROVAL = "approval"
    LATENCY = "latency"
