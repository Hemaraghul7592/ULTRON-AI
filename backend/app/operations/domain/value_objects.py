from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.operations.domain.enums import ComponentType, EnvironmentType, MetricType


class DomainModel(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls.model_validate(data)


class ConfidenceScore(DomainModel):
    value: float = Field(..., ge=0.0, le=1.0)


class RiskScore(DomainModel):
    value: float = Field(..., ge=0.0, le=100.0)


class ComponentDescriptor(DomainModel):
    component_type: ComponentType
    component_name: str = Field(..., min_length=1, max_length=100)


class EnvironmentDescriptor(DomainModel):
    environment_type: EnvironmentType
    name: str = Field(..., min_length=1, max_length=100)


class MetricDescriptor(DomainModel):
    metric_type: MetricType
    name: str = Field(..., min_length=1, max_length=100)


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


def utc_now() -> datetime:
    return datetime.now(UTC)
