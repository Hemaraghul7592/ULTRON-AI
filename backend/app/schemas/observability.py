from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class MetricCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    value: float
    unit: str | None = None
    tags: dict | None = None
    source: str | None = None


class MetricResponse(BaseModel):
    id: str
    name: str
    value: float
    unit: str | None = None
    tags_json: str | None = None
    source: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class MetricAggregation(BaseModel):
    name: str
    min_value: float
    max_value: float
    avg_value: float
    sum_value: float
    count: int
    period_start: datetime
    period_end: datetime


class DashboardResponse(BaseModel):
    total_conversations: int
    total_messages: int
    total_memories: int
    total_tasks: int
    total_tokens_used: int
    total_cost_usd: float
    active_tasks: int
    failed_jobs: int
    provider_usage: dict[str, int]
    recent_metrics: list[MetricResponse]
    latency_p50: float
    latency_p95: float
    latency_p99: float
    uptime_seconds: float
