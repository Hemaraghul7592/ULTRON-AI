from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ToolCallSchema(BaseModel):
    name: str
    arguments: dict


class ToolResultSchema(BaseModel):
    name: str
    result: str
    success: bool
    error: str | None = None
    execution_time_ms: float = 0.0


class PluginInfo(BaseModel):
    name: str
    version: str
    description: str
    tools: list[str]
    enabled: bool
    config: dict = {}


class PluginConfig(BaseModel):
    name: str
    enabled: bool = True
    config: dict = {}


class ToolInfo(BaseModel):
    name: str
    description: str
    plugin: str
    parameters: dict
    enabled: bool = True


class FileSourceRequest(BaseModel):
    source: str
    file_id: str | None = None
    file_path: str | None = None
    query: str | None = None


class FileSourceResponse(BaseModel):
    content: str
    source: str
    file_id: str | None = None
    file_name: str | None = None
    mime_type: str | None = None
    metadata: dict = {}
