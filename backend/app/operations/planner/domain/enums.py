from __future__ import annotations

from enum import StrEnum


class RepairStatus(StrEnum):
    DRAFT = "draft"
    CANDIDATES_GENERATED = "candidates_generated"
    SIMULATED = "simulated"
    RANKED = "ranked"
    VALIDATION_PENDING = "validation_pending"
    APPROVAL_PENDING = "approval_pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTION_READY = "execution_ready"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    FAILED = "failed"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    CATASTROPHIC = "catastrophic"


class ApprovalLevel(StrEnum):
    AUTO = "auto"
    MAINTAINER = "maintainer"
    SECURITY = "security"
    OPERATIONS = "operations"
    ADMINISTRATOR = "administrator"
    EMERGENCY_OVERRIDE = "emergency"
    BLOCKED = "blocked"


class RepairType(StrEnum):
    SERVICE_RESTART = "service_restart"
    CONFIGURATION_CHANGE = "configuration_change"
    DEPENDENCY_INSTALL = "dependency_install"
    RESOURCE_SCALING = "resource_scaling"
    DISK_CLEANUP = "disk_cleanup"
    NETWORK_CHECK = "network_check"
    DATABASE_MAINTENANCE = "database_maintenance"
    REDIS_MAINTENANCE = "redis_maintenance"
    DOCKER_RESTART = "docker_restart"
    DEPLOYMENT_ROLLBACK = "deployment_rollback"
    CODE_REVERT = "code_revert"
    ENVIRONMENT_VARIABLE_FIX = "environment_variable_fix"
    PERMISSION_FIX = "permission_fix"
    CACHE_CLEAR = "cache_clear"
    PROCESS_KILL = "process_kill"
    LOG_ROTATION = "log_rotation"
    MIGRATION_REPAIR = "migration_repair"
    MANUAL_INTERVENTION = "manual_intervention"


class RepairSource(StrEnum):
    RULE_BASED = "rule_based"
    HISTORICAL = "historical"
    COMPOSITE = "composite"


class ExecutionMode(StrEnum):
    IMMEDIATE = "immediate"
    SCHEDULED = "scheduled"
    QUEUED = "queued"
    MANUAL = "manual"


class ConstraintType(StrEnum):
    MAX_DOWNTIME = "max_downtime"
    NO_DATA_LOSS = "no_data_loss"
    REQUIRES_BACKUP = "requires_backup"
    PRODUCTION_ONLY = "production_only"
    MAINTENANCE_WINDOW = "maintenance_window"
    REQUIRES_HUMAN_APPROVAL = "requires_human_approval"
    EXTERNAL_DEPENDENCY_UNAVAILABLE = "external_dependency_unavailable"
    ENVIRONMENT_RESTRICTED = "environment_restricted"
    COMPONENT_EXCLUSION = "component_exclusion"
    TIME_WINDOW = "time_window"


class SimulationOutcome(StrEnum):
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"
    NO_IMPACT = "no_impact"
    UNKNOWN = "unknown"


class ValidationStage(StrEnum):
    PRE_SIMULATION = "pre_simulation"
    PRE_APPROVAL = "pre_approval"
    POST_EXECUTION = "post_execution"
    ROLLBACK_READINESS = "rollback_readiness"
    CONSTRAINT_VERIFICATION = "constraint_verification"


class RepairGraphNodeType(StrEnum):
    ACTION = "action"
    CHECK = "check"
    DECISION = "decision"
    PARALLEL_GROUP = "parallel_group"
    ROLLBACK = "rollback"
    VALIDATION = "validation"
