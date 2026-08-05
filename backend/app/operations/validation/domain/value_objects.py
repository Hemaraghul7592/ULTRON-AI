from __future__ import annotations

from datetime import datetime  # noqa: TC003
from typing import Any

from pydantic import Field, field_validator

from app.operations.domain.value_objects import DomainModel  # noqa: TC001


class ConfidenceScore(DomainModel):
    LOW_THRESHOLD: float = 0.3
    HIGH_THRESHOLD: float = 0.7

    value: float = Field(..., ge=0.0, le=1.0)

    @property
    def is_low(self) -> bool:
        return self.value < self.LOW_THRESHOLD

    @property
    def is_medium(self) -> bool:
        return self.LOW_THRESHOLD <= self.value < self.HIGH_THRESHOLD

    @property
    def is_high(self) -> bool:
        return self.value >= self.HIGH_THRESHOLD


class RiskScore(DomainModel):
    LOW_THRESHOLD: int = 30
    MEDIUM_THRESHOLD: int = 70
    HIGH_THRESHOLD: int = 90

    value: int = Field(..., ge=0, le=100)

    @property
    def is_low(self) -> bool:
        return self.value < self.LOW_THRESHOLD

    @property
    def is_medium(self) -> bool:
        return self.LOW_THRESHOLD <= self.value < self.MEDIUM_THRESHOLD

    @property
    def is_high(self) -> bool:
        return self.MEDIUM_THRESHOLD <= self.value < self.HIGH_THRESHOLD

    @property
    def is_catastrophic(self) -> bool:
        return self.value >= self.HIGH_THRESHOLD


class TimeRange(DomainModel):
    start: datetime
    end: datetime

    @field_validator("end")
    @classmethod
    def validate_order(cls, value: datetime, info: Any) -> datetime:
        start = info.data.get("start")
        if isinstance(start, datetime) and value < start:
            raise ValueError("end must be greater than or equal to start")
        return value

    @property
    def duration_seconds(self) -> float:
        return (self.end - self.start).total_seconds()

    def contains(self, dt: datetime) -> bool:
        return self.start <= dt <= self.end


class ThresholdRange(DomainModel):
    min_value: float
    max_value: float

    def contains(self, value: float) -> bool:
        return self.min_value <= value <= self.max_value


class ComponentDescriptor(DomainModel):
    name: str = Field(..., min_length=1, max_length=200)
    component_type: str = Field(..., min_length=1, max_length=100)
    environment: str = Field(..., min_length=1, max_length=100)
    version: str | None = Field(default=None, min_length=1, max_length=50)
    health_status: str | None = Field(default=None, min_length=1, max_length=50)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EnvironmentDescriptor(DomainModel):
    name: str = Field(..., min_length=1, max_length=200)
    is_production: bool
    allowed_actions: list[str] = Field(default_factory=list)
    restricted_actions: list[str] = Field(default_factory=list)
    required_approvals: list[str] = Field(default_factory=list)
    maintenance_window: MaintenanceWindow | None = None


class VersionConstraint(DomainModel):
    component: str = Field(..., min_length=1, max_length=200)
    constraint: str = Field(..., min_length=1, max_length=500)
    current_version: str = Field(..., min_length=1, max_length=50)
    required_version: str | None = Field(default=None, min_length=1, max_length=50)

    def is_satisfied_by(self, version: str) -> bool:
        raise NotImplementedError("TODO(v0.6): semantic version comparison")


class ResourceQuota(DomainModel):
    cpu_percent: ThresholdRange
    memory_mb: float = Field(default=0.0, ge=0.0)
    disk_gb: float = Field(default=0.0, ge=0.0)
    network_impact: str = Field(..., min_length=1, max_length=50)

    @classmethod
    def production_defaults(cls) -> ResourceQuota:
        return cls(
            cpu_percent=ThresholdRange(min_value=0, max_value=80),
            memory_mb=512,
            disk_gb=1,
            network_impact="low",
        )


class MaintenanceWindow(DomainModel):
    name: str = Field(..., min_length=1, max_length=200)
    schedule: str = Field(..., min_length=1, max_length=500)
    timezone: str = Field(..., min_length=1, max_length=100)
    allowed_actions: list[str] = Field(default_factory=list)
    blocked_actions: list[str] = Field(default_factory=list)

    def is_now_in_window(self) -> bool:
        raise NotImplementedError("TODO(v0.6): cron-based window check")
