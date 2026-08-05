from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.operations.incidents.domain.enums import RootCauseCategory
from app.operations.planner.domain.enums import RepairType


class RepairStrategy(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    id: str
    name: str
    description: str
    repair_type: RepairType
    root_cause_categories: list[RootCauseCategory] = Field(default_factory=list)
    environments: list[str] = Field(default_factory=list)
    severity_minimum: str = "info"
    steps_template: list[dict[str, str]] = Field(default_factory=list)
    estimated_duration_seconds: int = 300
    prerequisites: list[str] = Field(default_factory=list)
    affected_components: list[str] = Field(default_factory=list)
    auto_approvable_environments: list[str] = Field(default_factory=list)


_STRATEGIES: list[RepairStrategy] = [
    RepairStrategy(
        id="S01",
        name="Restart Backend Service",
        description="Restart the backend API service to resolve transient issues",
        repair_type=RepairType.SERVICE_RESTART,
        root_cause_categories=[RootCauseCategory.CODE, RootCauseCategory.CONFIGURATION],
        environments=["development", "staging", "production"],
        severity_minimum="warning",
        steps_template=[
            {"action": "stop_service", "target": "backend"},
            {"action": "verify_stopped", "target": "backend"},
            {"action": "start_service", "target": "backend"},
            {"action": "health_check", "target": "backend"},
        ],
        estimated_duration_seconds=120,
        affected_components=["backend"],
        auto_approvable_environments=["development", "staging"],
    ),
    RepairStrategy(
        id="S02",
        name="Restart Database",
        description="Restart the database container to resolve connection issues",
        repair_type=RepairType.DATABASE_MAINTENANCE,
        root_cause_categories=[RootCauseCategory.DATABASE],
        environments=["development", "staging"],
        severity_minimum="warning",
        steps_template=[
            {"action": "stop_container", "target": "database"},
            {"action": "start_container", "target": "database"},
            {"action": "connectivity_check", "target": "database"},
        ],
        estimated_duration_seconds=180,
        affected_components=["database"],
    ),
    RepairStrategy(
        id="S03",
        name="Restart Redis",
        description="Restart the Redis cache to resolve connection issues",
        repair_type=RepairType.REDIS_MAINTENANCE,
        root_cause_categories=[RootCauseCategory.REDIS],
        environments=["development", "staging"],
        severity_minimum="warning",
        steps_template=[
            {"action": "stop_container", "target": "redis"},
            {"action": "start_container", "target": "redis"},
            {"action": "ping_check", "target": "redis"},
        ],
        estimated_duration_seconds=120,
        affected_components=["redis"],
    ),
    RepairStrategy(
        id="S04",
        name="Free Disk Space",
        description="Clean up disk space by archiving or deleting large files",
        repair_type=RepairType.DISK_CLEANUP,
        root_cause_categories=[RootCauseCategory.DISK],
        environments=["development", "staging", "production"],
        severity_minimum="warning",
        steps_template=[
            {"action": "identify_large_files", "target": "disk"},
            {"action": "archive_or_delete", "target": "disk"},
            {"action": "verify_space", "target": "disk"},
        ],
        estimated_duration_seconds=300,
        affected_components=["disk"],
        auto_approvable_environments=["development"],
    ),
    RepairStrategy(
        id="S05",
        name="Scale CPU Resources",
        description="Adjust CPU resource limits to handle load",
        repair_type=RepairType.RESOURCE_SCALING,
        root_cause_categories=[RootCauseCategory.CPU],
        environments=["development", "staging"],
        severity_minimum="warning",
        steps_template=[
            {"action": "check_limits", "target": "cpu"},
            {"action": "adjust_limits", "target": "cpu"},
            {"action": "verify_usage", "target": "cpu"},
        ],
        estimated_duration_seconds=180,
        affected_components=["cpu"],
    ),
    RepairStrategy(
        id="S06",
        name="Scale Memory Resources",
        description="Adjust memory resource limits to handle pressure",
        repair_type=RepairType.RESOURCE_SCALING,
        root_cause_categories=[RootCauseCategory.MEMORY],
        environments=["development", "staging"],
        severity_minimum="warning",
        steps_template=[
            {"action": "check_limits", "target": "memory"},
            {"action": "adjust_limits", "target": "memory"},
            {"action": "verify_usage", "target": "memory"},
        ],
        estimated_duration_seconds=180,
        affected_components=["memory"],
    ),
    RepairStrategy(
        id="S07",
        name="Check Network",
        description="Verify network connectivity and DNS resolution",
        repair_type=RepairType.NETWORK_CHECK,
        root_cause_categories=[RootCauseCategory.NETWORK],
        environments=["development", "staging", "production"],
        severity_minimum="warning",
        steps_template=[
            {"action": "ping_endpoints", "target": "network"},
            {"action": "check_dns", "target": "network"},
            {"action": "verify_connectivity", "target": "network"},
        ],
        estimated_duration_seconds=60,
        affected_components=["network"],
        auto_approvable_environments=["development", "staging", "production"],
    ),
    RepairStrategy(
        id="S08",
        name="Install Missing Dependency",
        description="Install missing Python dependencies",
        repair_type=RepairType.DEPENDENCY_INSTALL,
        root_cause_categories=[RootCauseCategory.DEPENDENCY],
        environments=["development", "staging"],
        severity_minimum="warning",
        steps_template=[
            {"action": "identify_missing", "target": "dependency"},
            {"action": "install", "target": "dependency"},
            {"action": "verify_import", "target": "dependency"},
        ],
        estimated_duration_seconds=120,
        affected_components=["backend"],
    ),
    RepairStrategy(
        id="S09",
        name="Fix Configuration",
        description="Fix configuration errors and restart affected service",
        repair_type=RepairType.CONFIGURATION_CHANGE,
        root_cause_categories=[RootCauseCategory.CONFIGURATION],
        environments=["development", "staging", "production"],
        severity_minimum="warning",
        steps_template=[
            {"action": "identify_misconfig", "target": "config"},
            {"action": "update_config", "target": "config"},
            {"action": "restart_service", "target": "backend"},
        ],
        estimated_duration_seconds=180,
        affected_components=["backend", "config"],
    ),
    RepairStrategy(
        id="S10",
        name="Rollback Deployment",
        description="Rollback to the last known good deployment",
        repair_type=RepairType.DEPLOYMENT_ROLLBACK,
        root_cause_categories=[RootCauseCategory.DEPLOYMENT, RootCauseCategory.CODE],
        environments=["development", "staging", "production"],
        severity_minimum="high",
        steps_template=[
            {"action": "identify_last_good", "target": "deployment"},
            {"action": "rollback", "target": "deployment"},
            {"action": "verify_health", "target": "backend"},
        ],
        estimated_duration_seconds=300,
        affected_components=["backend", "deployment"],
    ),
    RepairStrategy(
        id="S11",
        name="Revert Code Change",
        description="Revert the last code change that introduced the issue",
        repair_type=RepairType.CODE_REVERT,
        root_cause_categories=[RootCauseCategory.CODE],
        environments=["development", "staging"],
        severity_minimum="high",
        steps_template=[
            {"action": "identify_bad_commit", "target": "code"},
            {"action": "revert", "target": "code"},
            {"action": "restart_service", "target": "backend"},
        ],
        estimated_duration_seconds=180,
        affected_components=["backend", "code"],
    ),
    RepairStrategy(
        id="S12",
        name="Fix Environment Variable",
        description="Set missing or incorrect environment variable",
        repair_type=RepairType.ENVIRONMENT_VARIABLE_FIX,
        root_cause_categories=[RootCauseCategory.CONFIGURATION],
        environments=["development", "staging", "production"],
        severity_minimum="warning",
        steps_template=[
            {"action": "identify_missing", "target": "env_var"},
            {"action": "set_variable", "target": "env_var"},
            {"action": "restart_service", "target": "backend"},
        ],
        estimated_duration_seconds=120,
        affected_components=["backend", "config"],
    ),
    RepairStrategy(
        id="S13",
        name="Restart Docker Container",
        description="Restart an unhealthy Docker container",
        repair_type=RepairType.DOCKER_RESTART,
        root_cause_categories=[RootCauseCategory.DEPENDENCY],
        environments=["development", "staging", "production"],
        severity_minimum="warning",
        steps_template=[
            {"action": "stop_container", "target": "container"},
            {"action": "start_container", "target": "container"},
            {"action": "health_check", "target": "container"},
        ],
        estimated_duration_seconds=120,
        affected_components=["docker"],
    ),
    RepairStrategy(
        id="S14",
        name="Clear Cache",
        description="Clear Redis cache to resolve stale data issues",
        repair_type=RepairType.CACHE_CLEAR,
        root_cause_categories=[RootCauseCategory.REDIS, RootCauseCategory.CONFIGURATION],
        environments=["development", "staging", "production"],
        severity_minimum="warning",
        steps_template=[
            {"action": "flush_cache", "target": "redis"},
            {"action": "verify_cache_empty", "target": "redis"},
            {"action": "reload_config", "target": "backend"},
        ],
        estimated_duration_seconds=60,
        affected_components=["redis"],
        auto_approvable_environments=["development", "staging"],
    ),
    RepairStrategy(
        id="S15",
        name="Kill Stuck Process",
        description="Kill a stuck or unresponsive process",
        repair_type=RepairType.PROCESS_KILL,
        root_cause_categories=[RootCauseCategory.CODE, RootCauseCategory.DEPENDENCY],
        environments=["development", "staging"],
        severity_minimum="warning",
        steps_template=[
            {"action": "identify_process", "target": "process"},
            {"action": "kill", "target": "process"},
            {"action": "verify_cleanup", "target": "process"},
        ],
        estimated_duration_seconds=60,
        affected_components=["backend"],
    ),
    RepairStrategy(
        id="S16",
        name="Rotate Logs",
        description="Archive and truncate log files to free disk space",
        repair_type=RepairType.LOG_ROTATION,
        root_cause_categories=[RootCauseCategory.DISK],
        environments=["development", "staging", "production"],
        severity_minimum="warning",
        steps_template=[
            {"action": "archive_logs", "target": "logs"},
            {"action": "truncate", "target": "logs"},
            {"action": "verify_disk", "target": "disk"},
        ],
        estimated_duration_seconds=120,
        affected_components=["disk"],
        auto_approvable_environments=["development", "staging", "production"],
    ),
    RepairStrategy(
        id="S17",
        name="Repair Migration",
        description="Repair or rollback a failed database migration",
        repair_type=RepairType.MIGRATION_REPAIR,
        root_cause_categories=[RootCauseCategory.DATABASE],
        environments=["development", "staging"],
        severity_minimum="high",
        steps_template=[
            {"action": "check_state", "target": "database"},
            {"action": "repair_or_rollback", "target": "database"},
            {"action": "verify_schema", "target": "database"},
        ],
        estimated_duration_seconds=300,
        affected_components=["database"],
    ),
    RepairStrategy(
        id="S18",
        name="Manual Intervention Required",
        description="Create a ticket and notify the team for manual intervention",
        repair_type=RepairType.MANUAL_INTERVENTION,
        root_cause_categories=[RootCauseCategory.UNKNOWN],
        environments=["development", "staging", "production"],
        severity_minimum="info",
        steps_template=[
            {"action": "create_ticket", "target": "ticketing"},
            {"action": "notify_team", "target": "notification"},
        ],
        estimated_duration_seconds=60,
        affected_components=[],
    ),
]


def get_all_strategies() -> list[RepairStrategy]:
    return list(_STRATEGIES)


def get_strategies_for_category(category: RootCauseCategory) -> list[RepairStrategy]:
    return [s for s in _STRATEGIES if category in s.root_cause_categories]
