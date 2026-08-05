from __future__ import annotations

from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class ValidateRequestDTO(BaseModel):
    """DTO for submitting a validation request."""

    model_config = ConfigDict(frozen=True)

    plan_id: str = Field(..., min_length=1, max_length=100)
    incident_id: str | None = Field(default=None, min_length=1, max_length=100)
    environment: str = Field(..., min_length=1, max_length=100)
    requested_by: str = Field(..., min_length=1, max_length=200)
    priority: int = Field(default=0, ge=0, le=100)
    timeout_seconds: int = Field(default=300, ge=1, le=3600)
    plan_type: str = Field(default="infrastructure_repair", min_length=1, max_length=100)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExplainRequestDTO(BaseModel):
    """DTO for requesting a detailed validation explanation."""

    model_config = ConfigDict(frozen=True)

    request_id: str = Field(..., min_length=1, max_length=100)
    plan_id: str = Field(..., min_length=1, max_length=100)
    include_evidence: bool = False
    include_factors: bool = False


class ValidationStatusRequestDTO(BaseModel):
    """DTO for querying validation status."""

    model_config = ConfigDict(frozen=True)

    request_id: str = Field(..., min_length=1, max_length=100)
    plan_id: str | None = Field(default=None, min_length=1, max_length=100)


class BatchValidationRequestDTO(BaseModel):
    """DTO for submitting multiple validation requests at once."""

    model_config = ConfigDict(frozen=True)

    requests: list[ValidateRequestDTO] = Field(min_length=1)
    batch_id: str = Field(default_factory=lambda: str(uuid4()), min_length=1, max_length=100)
    metadata: dict[str, Any] = Field(default_factory=dict)
