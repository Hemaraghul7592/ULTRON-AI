# AI Engine — ULTRON AI Platform

## Architecture

```
┌─────────────────┐
│   ChatService    │
│  (Single entry)  │
└───────┬─────────┘
        │
        ▼
┌─────────────────────┐
│  Prompt Builder      │
│  - System prompt     │
│  - Memory context    │
│  - Conversation      │
│  - Tool definitions  │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│     AIService       │
│  (Provider gateway) │
│                     │
│  - Provider select  │
│  - Fallback logic   │
│  - Error normalize  │
│  - Metrics          │
└─────────┬───────────┘
          │
     ┌────┴────┐
     ▼         ▼
┌─────────┐ ┌─────────┐
│ OpenAI   │ │ Gemini  │
│ Groq     │ │         │
│ Grok     │ │         │
└────┬────┘ └────┬────┘
     │           │
     ▼           ▼
┌─────────────────────┐
│  Response Handler    │
│  - Parse tool calls  │
│  - Execute tools     │
│  - Stream tokens     │
│  - Return result     │
└─────────────────────┘
```

## Provider Interface

```python
class AIProvider(ABC):
    """Abstract interface for all AI providers."""

    @abstractmethod
    async def chat(
        self,
        messages: list[dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: list[dict] | None = None,
    ) -> dict[str, Any]: ...

    @abstractmethod
    async def chat_stream(
        self,
        messages: list[dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: list[dict] | None = None,
    ) -> AsyncIterator[dict[str, Any]]: ...

    @abstractmethod
    def is_available(self) -> bool: ...

    @abstractmethod
    def get_models(self) -> list[str]: ...
```

## Supported Providers

| Provider | Models | Streaming | Tools |
|----------|--------|-----------|-------|
| OpenAI | GPT-4o, GPT-4o-mini, GPT-4-turbo | ✅ | ✅ |
| Groq | Llama 3, Mixtral, Gemma | ✅ | ✅ |
| Gemini | Gemini 2.0 Flash, 1.5 Pro | ✅ | ✅ |
| Grok (xAI) | Grok-2, Grok-2 Vision | ✅ | ✅ |

## Error Hierarchy

```
UltronException
├── AIServiceException          # General AI error
│   ├── ProviderUnavailableException  # Provider down/unconfigured
│   ├── AIAuthenticationException     # Invalid API key (401)
│   ├── AIRateLimitException          # Rate limited (429)
│   └── AIContextLengthException      # Context too long (400)
├── ToolExecutionException
├── RateLimitException
└── ...
```

### Error Mapping (OpenAI-Compatible)

| HTTP Status | Exception |
|-------------|-----------|
| 401         | AIAuthenticationException |
| 429         | AIRateLimitException |
| 400 (context_length) | AIContextLengthException |
| Other       | AIServiceException |

## Configuration

```python
# .env
GROQ_API_KEY="gsk_..."
GROQ_MODEL="llama-3.3-70b-versatile"
GEMINI_API_KEY="AIza..."
GEMINI_MODEL="gemini-2.0-flash"
OPENAI_API_KEY="sk-..."
OPENAI_MODEL="gpt-4o-mini"
GROK_API_KEY="xai-..."
GROK_MODEL="grok-2-latest"
DEFAULT_AI_PROVIDER="groq"
```

## AIService — Single Entry Point

```python
class AIService:
    """Single gateway for all AI requests."""

    async def chat(
        messages: list[dict],
        provider: str | None = None,
        fallback: list[str] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: list[dict] | None = None,
    ) -> dict: ...

    async def chat_stream(
        messages: list[dict],
        provider: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: list[dict] | None = None,
    ) -> AsyncIterator[dict]: ...

    def get_available_providers() -> list[dict]: ...
```

### Fallback Logic

```
chat(messages, provider="groq", fallback=["openai", "gemini"]):
  if groq available → try groq
  on error → try openai
  on error → try gemini
  all fail → raise last error

chat(messages, provider="groq"):  # no fallback
  if groq available → try groq
  if not configured → raise ProviderUnavailableException
```

## Streaming Protocol (SSE)

```
GET /api/v1/chat/stream

Event: chunk
data: {"content": "Hello", "index": 0, "finish_reason": null}

Event: chunk
data: {"content": " world", "index": 1, "finish_reason": null}

Event: chunk
data: {"content": "", "index": 2, "finish_reason": "stop", "usage": {...}}

Event: done
data: {"conversation_id": "uuid", "tokens_used": 42, "latency_ms": 1234}
```

## Model Registry

```json
{
  "openai": {
    "gpt-4o": {
      "context": 128000,
      "capabilities": ["chat", "tools", "streaming", "vision"],
      "performance_tier": "high"
    },
    "gpt-4o-mini": {
      "context": 128000,
      "capabilities": ["chat", "tools", "streaming", "vision"],
      "performance_tier": "medium"
    }
  },
  "groq": {
    "llama-3.3-70b-versatile": {
      "context": 32768,
      "capabilities": ["chat", "tools", "streaming"],
      "performance_tier": "high"
    },
    "mixtral-8x7b-32768": {
      "context": 32768,
      "capabilities": ["chat", "tools", "streaming"],
      "performance_tier": "medium"
    }
  },
  "gemini": {
    "gemini-2.0-flash": {
      "context": 1048576,
      "capabilities": ["chat", "tools", "streaming", "vision"],
      "performance_tier": "high"
    }
  },
  "grok": {
    "grok-2-latest": {
      "context": 131072,
      "capabilities": ["chat", "tools", "streaming"],
      "performance_tier": "high"
    }
  }
}
```

## Prompt Management

### System Prompt Template

```
You are ULTRON AI, a helpful AI assistant.

## Context
Current time: {current_time}
User info: {user_info}

## Memory
{relevant_memories}

## Capabilities
{tool_descriptions}

## Instructions
{user_system_prompt or default}
```

### Override Strategy

- User can set a custom system prompt per conversation
- User can set a global default system prompt in settings
- Base system prompt is always prepended (non-overridable security context)

## Token Budget Management

```python
TOKEN_BUDGET = {
    "system": 500,
    "conversation": 2000,
    "memory_context": 1000,
    "tool_results": 500,
    "reserve": 96,
}

def build_prompt(conversation, memories, tools):
    budget = TokenBudget(TOKEN_BUDGET)

    # System prompt (always included)
    system = build_system_prompt(tools)
    budget.use("system", count_tokens(system))

    # Conversation messages (trim from oldest)
    messages = trim_to_budget(conversation.messages, budget.remaining("conversation"))

    # Memory context (rank and include highest)
    memory_context = select_memories(memories, budget.remaining("memory_context"))

    return Prompt(system=system, messages=messages, memories=memory_context)
```

## Unified Response Format

```json
{
  "id": "msg_uuid",
  "conversation_id": "conv_uuid",
  "role": "assistant",
  "content": "Here's the answer to your question...",
  "model": "llama-3.3-70b-versatile",
  "provider": "groq",
  "tokens_used": {
    "prompt": 456,
    "completion": 123,
    "total": 579
  },
  "latency_ms": 2345,
  "tool_calls": [
    {
      "id": "call_uuid",
      "type": "function",
      "function": {
        "name": "search_web",
        "arguments": {"query": "latest AI news 2026"}
      }
    }
  ]
}
```
