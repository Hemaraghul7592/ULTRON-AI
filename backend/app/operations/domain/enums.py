from __future__ import annotations

from enum import Enum


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    OFFLINE = "offline"


class IncidentSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(str, Enum):
    OPEN = "open"
    TRIAGED = "triaged"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    ROLLED_BACK = "rolled_back"
    ESCALATED = "escalated"


class ComponentType(str, Enum):
    BACKEND = "backend"
    DATABASE = "database"
    REDIS = "redis"
    GITHUB_ACTIONS = "github_actions"
    DOCKER = "docker"
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    API = "api"


class EnvironmentType(str, Enum):
    DEVELOPMENT = "development"
    TEST = "test"
    STAGING = "staging"
    PRODUCTION = "production"


class MetricType(str, Enum):
    CPU_PERCENT = "cpu_percent"
    MEMORY_PERCENT = "memory_percent"
    DISK_PERCENT = "disk_percent"
    API_LATENCY_MS = "api_latency_ms"
    RESPONSE_TIME_MS = "response_time_ms"
    DATABASE_LATENCY_MS = "database_latency_ms"
    REQUEST_COUNT = "request_count"
    ERROR_RATE = "error_rate"


class EvidenceType(str, Enum):
    FASTAPI_LOG = "fastapi_log"
    STACK_TRACE = "stack_trace"
    DOCKER_LOG = "docker_log"
    GITHUB_ACTIONS_LOG = "github_actions_log"
    SYSTEM_LOG = "system_log"
    METRIC_SNAPSHOT = "metric_snapshot"
    COMMITS = "commits"
    CONFIGURATION = "configuration"
    ENVIRONMENT_VARIABLES = "environment_variables"


class EventType(str, Enum):
    HEALTH_SNAPSHOT_RECORDED = "health_snapshot_recorded"
    COMPONENT_DEGRADED = "component_degraded"
    INCIDENT_CREATED = "incident_created"
    INCIDENT_RESOLVED = "incident_resolved"
    EVIDENCE_COLLECTED = "evidence_collected"
    METRICS_RECORDED = "metrics_recorded"
    DIAGNOSTIC_PACK_GENERATED = "diagnostic_pack_generated"
    KNOWLEDGE_ENTRY_CREATED = "knowledge_entry_created"
