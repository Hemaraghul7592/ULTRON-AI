from __future__ import annotations

from datetime import datetime  # noqa: TC003
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from app.operations.domain.value_objects import utc_now  # noqa: TC001
from app.operations.validation.domain.enums import BlockerType  # noqa: TC001


class ExecutionPermission(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    permission_id: str = Field(default_factory=lambda: str(uuid4()), min_length=1, max_length=100)
    plan_id: str = Field(..., min_length=1, max_length=100)
    result_id: str = Field(..., min_length=1, max_length=100)
    granted: bool
    granted_by: str = Field(..., min_length=1, max_length=200)
    granted_at: datetime = Field(default_factory=utc_now)
    expires_at: datetime
    conditions: list[str] = Field(default_factory=list)
    signature_id: str | None = Field(default=None, min_length=1, max_length=100)
    revocation_reason: str | None = None
    revoked_at: datetime | None = None
    created_at: datetime = Field(default_factory=utc_now)


class ExecutionBlocker(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    blocker_id: str = Field(default_factory=lambda: str(uuid4()), min_length=1, max_length=100)
    plan_id: str = Field(..., min_length=1, max_length=100)
    result_id: str = Field(..., min_length=1, max_length=100)
    blocker_type: BlockerType
    reason: str = Field(..., min_length=1, max_length=1000)
    rule_code: str | None = Field(default=None, min_length=1, max_length=100)
    policy_id: str | None = Field(default=None, min_length=1, max_length=100)
    resolved_at: datetime | None = None
    created_at: datetime = Field(default_factory=utc_now)
