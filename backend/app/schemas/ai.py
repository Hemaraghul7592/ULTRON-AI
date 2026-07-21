from __future__ import annotations

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str
    content: str
    name: str | None = None
    tool_call_id: str | None = None
    tool_calls: list[dict] | None = None


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=100000)
    conversation_id: str | None = None
    system_prompt: str | None = None
    model: str | None = None
    provider: str | None = None
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=1, le=32768)
    stream: bool = False
    use_memory: bool = True
    use_tools: bool = True
    context: dict | None = None


class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: dict


class ToolCall(BaseModel):
    id: str
    name: str
    arguments: dict


class ToolResult(BaseModel):
    tool_call_id: str
    name: str
    result: str
    success: bool
    error: str | None = None


class ChatResponse(BaseModel):
    message: str
    conversation_id: str
    message_id: str
    model: str
    provider: str
    tokens_used: int
    prompt_tokens: int
    completion_tokens: int
    tool_calls: list[ToolCall] = []
    tool_results: list[ToolResult] = []
    latency_ms: float
    finish_reason: str = "stop"


class StreamChunk(BaseModel):
    content: str = ""
    done: bool = False
    tool_calls: list[ToolCall] = []
    tokens_used: int = 0
    finish_reason: str | None = None


class AIProviderConfig(BaseModel):
    provider: str
    model: str | None = None
    api_key: str | None = None
    temperature: float = 0.7
    max_tokens: int = 4096
    system_prompt: str | None = None


class AIProviderInfo(BaseModel):
    name: str
    available: bool
    models: list[str]
    default_model: str
