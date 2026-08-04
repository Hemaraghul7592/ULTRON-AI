from __future__ import annotations

from datetime import datetime  # noqa: TC003

from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    priority: int = Field(default=0, ge=0, le=10)
    due_date: datetime | None = None
    recurring_cron: str | None = None
    tags: list[str] = []


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = Field(default=None, pattern="^(pending|in_progress|completed|cancelled)$")
    priority: int | None = Field(default=None, ge=0, le=10)
    due_date: datetime | None = None
    recurring_cron: str | None = None


class TaskResponse(BaseModel):
    id: str
    title: str
    description: str | None = None
    status: str
    priority: int
    due_date: datetime | None = None
    completed_at: datetime | None = None
    recurring_cron: str | None = None
    tags_json: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TaskListResponse(BaseModel):
    tasks: list[TaskResponse]
    total: int
    page: int
    page_size: int


class JobResponse(BaseModel):
    id: str
    name: str
    job_type: str
    status: str
    payload: str | None = None
    result: str | None = None
    error_message: str | None = None
    attempts: int
    max_attempts: int
    scheduled_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
