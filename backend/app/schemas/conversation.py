from __future__ import annotations

from datetime import datetime  # noqa: TC003

from pydantic import BaseModel, Field


class ConversationCreate(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    model: str | None = Field(default=None, max_length=100)
    system_prompt: str | None = Field(default=None, max_length=10000)


class ConversationUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    model: str | None = Field(default=None, max_length=100)
    system_prompt: str | None = Field(default=None, max_length=10000)


class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=100000)
    role: str = Field(default="user", pattern="^(user|assistant|system|tool)$")


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    model: str | None = None
    tokens_used: int | None = None
    tool_calls: str | None = None
    metadata_json: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationResponse(BaseModel):
    id: str
    title: str | None = None
    model: str | None = None
    system_prompt: str | None = None
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

    model_config = {"from_attributes": True}


class ConversationDetailResponse(ConversationResponse):
    messages: list[MessageResponse] = []


class ConversationListResponse(BaseModel):
    conversations: list[ConversationResponse]
    total: int
    page: int
    page_size: int
