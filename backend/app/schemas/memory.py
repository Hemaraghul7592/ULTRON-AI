from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

CATEGORY_PATTERN = "^(general|user_profile|preference|project|conversation)$"


class TagCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class TagResponse(BaseModel):
    id: str
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}


class MemoryCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=50000)
    memory_type: str = Field(
        default="short_term", pattern="^(short_term|long_term|episodic|semantic)$",
    )
    category: str = Field(default="general", pattern=CATEGORY_PATTERN)
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    source: str | None = Field(default=None, max_length=100)
    context: str | None = Field(default=None, max_length=10000)
    tags: list[str] = Field(default_factory=list, max_length=50)


class MemoryUpdate(BaseModel):
    content: str | None = Field(default=None, min_length=1, max_length=50000)
    summary: str | None = Field(default=None, max_length=10000)
    memory_type: str | None = Field(
        default=None, pattern="^(short_term|long_term|episodic|semantic)$",
    )
    category: str | None = Field(default=None, pattern=CATEGORY_PATTERN)
    importance: float | None = Field(default=None, ge=0.0, le=1.0)
    is_archived: bool | None = None
    tags: list[str] | None = Field(default=None, max_length=50)


class MemoryResponse(BaseModel):
    id: str
    content: str
    summary: str | None = None
    memory_type: str
    category: str = "general"
    is_archived: bool = False
    importance: float
    access_count: int
    source: str | None = None
    context: str | None = None
    tags: list[TagResponse] = []
    created_at: datetime
    updated_at: datetime
    last_accessed: datetime

    model_config = {"from_attributes": True}


class MemoryListResponse(BaseModel):
    memories: list[MemoryResponse]
    total: int
    page: int
    page_size: int


class MemorySearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    memory_type: str | None = Field(
        default=None, pattern="^(short_term|long_term|episodic|semantic)$",
    )
    category: str | None = Field(default=None, pattern=CATEGORY_PATTERN)
    limit: int = Field(default=10, ge=1, le=50)
    min_importance: float = Field(default=0.0, ge=0.0, le=1.0)


class MemorySearchResponse(BaseModel):
    memories: list[MemoryResponse]
    scores: list[float]
    query: str
