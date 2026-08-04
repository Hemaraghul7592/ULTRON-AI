from __future__ import annotations

from enum import StrEnum


class HealthStatus(StrEnum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    OFFLINE = "offline"
    NOT_CONFIGURED = "not_configured"


class IncidentSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(StrEnum):
    OPEN = "open"
    TRIAGED = "triaged"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    ROLLED_BACK = "rolled_back"
    ESCALATED = "escalated"


class ComponentType(StrEnum):
    BACKEND = "backend"
    DATABASE = "database"
    REDIS = "redis"
    GITHUB_ACTIONS = "github_actions"
    DOCKER = "docker"
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    API = "api"
    NETWORK = "network"


class EnvironmentType(StrEnum):
    DEVELOPMENT = "development"
    TEST = "test"
    STAGING = "staging"
    PRODUCTION = "production"


class MetricType(StrEnum):
    CPU_PERCENT = "cpu_percent"
    MEMORY_PERCENT = "memory_percent"
    DISK_PERCENT = "disk_percent"
    API_LATENCY_MS = "api_latency_ms"
    RESPONSE_TIME_MS = "response_time_ms"
    DATABASE_LATENCY_MS = "database_latency_ms"
    REQUEST_COUNT = "request_count"
    ERROR_RATE = "error_rate"


class EvidenceType(StrEnum):
    FASTAPI_LOG = "fastapi_log"
    STACK_TRACE = "stack_trace"
    DOCKER_LOG = "docker_log"
    GITHUB_ACTIONS_LOG = "github_actions_log"
    SYSTEM_LOG = "system_log"
    METRIC_SNAPSHOT = "metric_snapshot"
    COMMITS = "commits"
    CONFIGURATION = "configuration"
    ENVIRONMENT_VARIABLES = "environment_variables"


class EventType(StrEnum):
    HEALTH_SNAPSHOT_RECORDED = "health_snapshot_recorded"
    HEALTH_CHECK_STARTED = "health_check_started"
    HEALTH_CHECK_COMPLETED = "health_check_completed"
    COMPONENT_HEALTHY = "component_healthy"
    COMPONENT_WARNING = "component_warning"
    COMPONENT_CRITICAL = "component_critical"
    COMPONENT_OFFLINE = "component_offline"
    COMPONENT_NOT_CONFIGURED = "component_not_configured"
    COMPONENT_DEGRADED = "component_degraded"
    INCIDENT_CREATED = "incident_created"
    INCIDENT_RESOLVED = "incident_resolved"
    EVIDENCE_COLLECTED = "evidence_collected"
    METRICS_RECORDED = "metrics_recorded"
    DIAGNOSTIC_PACK_GENERATED = "diagnostic_pack_generated"
    KNOWLEDGE_ENTRY_CREATED = "knowledge_entry_created"
