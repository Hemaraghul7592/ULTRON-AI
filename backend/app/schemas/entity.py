from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class EntityCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    entity_type: str = Field(..., min_length=1, max_length=50)
    description: str | None = None
    properties: dict | None = None


class EntityResponse(BaseModel):
    id: str
    name: str
    entity_type: str
    description: str | None = None
    properties_json: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RelationshipCreate(BaseModel):
    source_id: str
    target_id: str
    relation_type: str = Field(..., min_length=1, max_length=100)
    weight: float = Field(default=1.0, ge=0.0, le=10.0)
    properties: dict | None = None


class RelationshipResponse(BaseModel):
    id: str
    source_id: str
    target_id: str
    relation_type: str
    weight: float
    properties_json: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class KnowledgeGraphResponse(BaseModel):
    entities: list[EntityResponse]
    relationships: list[RelationshipResponse]
    total_entities: int
    total_relationships: int
