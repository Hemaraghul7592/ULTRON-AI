from __future__ import annotations

from enum import StrEnum


class IncidentStatus(StrEnum):
    DETECTED = "detected"
    INVESTIGATING = "investigating"
    EVIDENCE_COLLECTED = "evidence_collected"
    ANALYZING = "analyzing"
    ROOT_CAUSE_FOUND = "root_cause_found"
    WAITING_FOR_REPAIR = "waiting_for_repair"
    RESOLVED = "resolved"
    FAILED = "failed"


class IncidentSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class InvestigationStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class EvidenceCategory(StrEnum):
    LOG = "log"
    METRIC = "metric"
    CONFIG = "config"
    SYSTEM = "system"
    DEPLOYMENT = "deployment"
    EXTERNAL = "external"
    STATE = "state"


class RootCauseCategory(StrEnum):
    DATABASE = "database"
    REDIS = "redis"
    NETWORK = "network"
    MEMORY = "memory"
    CPU = "cpu"
    DISK = "disk"
    DEPENDENCY = "dependency"
    CONFIGURATION = "configuration"
    DEPLOYMENT = "deployment"
    CODE = "code"
    UNKNOWN = "unknown"


class RecommendedAction(StrEnum):
    RESTART_SERVICE = "restart_service"
    RESTART_DATABASE = "restart_database"
    RESTART_REDIS = "restart_redis"
    SCALE_RESOURCES = "scale_resources"
    FREE_DISK_SPACE = "free_disk_space"
    CHECK_NETWORK = "check_network"
    INSTALL_DEPENDENCY = "install_dependency"
    FIX_CONFIGURATION = "fix_configuration"
    ROLLBACK_DEPLOYMENT = "rollback_deployment"
    REVERT_CODE = "revert_code"
    INVESTIGATE_MANUALLY = "investigate_manually"
    NO_ACTION = "no_action"
