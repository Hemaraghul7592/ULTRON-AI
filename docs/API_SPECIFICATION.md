# API Specification — ULTRON AI Platform

## Design Principles

1. **RESTful** resources with consistent URL patterns
2. **Versioned** via URL prefix (`/api/v1/`, future `/api/v2/`)
3. **Pagination** via cursor-based for streams, offset-based for lists
4. **Errors** follow RFC 7807 (Problem Details)
5. **Authentication** via JWT Bearer tokens with refresh token rotation
6. **Streaming** via SSE for AI responses, WebSocket for real-time events

## Base URL

```
Production:  https://api.ultron.ai/api/v1
Local:       http://127.0.0.1:8000/api/v1
```

## Authentication

### Token Flow

```
┌─────────┐          ┌─────────┐          ┌─────────┐
│ Client  │          │  Auth   │          │ Backend │
│         │          │ Provider│          │         │
├─────────┤          ├─────────┤          ├─────────┤
│ POST /login ──────►│         │          │         │
│◄──── access_token  │         │          │         │
│◄──── refresh_token │         │          │         │
├─────────┤          ├─────────┤          ├─────────┤
│ POST /refresh ────►│         │          │         │
│◄──── new tokens    │         │          │         │
└─────────┘          └─────────┘          └─────────┘
```

### Headers

```
Authorization: Bearer <access_token>
X-Request-ID: <uuid>        (idempotency, debugging)
X-Client-Version: <semver>  (feature detection)
X-Platform: android|ios|macos|windows
```

## Standard Error Format

```json
{
  "type": "https://api.ultron.ai/errors/validation-error",
  "title": "Validation Error",
  "status": 422,
  "detail": "The request body contains invalid fields.",
  "instance": "/api/v1/chat",
  "errors": [
    {
      "field": "message.content",
      "message": "String must have at least 1 character"
    }
  ]
}
```

## Endpoint Reference

### Auth (`/auth`)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/auth/register` | Create account | No |
| POST | `/auth/login` | Login, returns token pair | No |
| POST | `/auth/refresh` | Refresh access token | Refresh |
| POST | `/auth/logout` | Invalidate refresh token | Bearer |
| GET  | `/auth/verify` | Check token validity | Bearer |
| POST | `/auth/change-password` | Change password | Bearer |
| POST | `/auth/forgot-password` | Request password reset | No |
| POST | `/auth/reset-password` | Reset with token | No |

### Chat (`/chat`)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/chat` | Send message, get response | Bearer |
| POST | `/chat/stream` | Send message, stream response (SSE) | Bearer |
| POST | `/chat/stop` | Stop active generation | Bearer |
| GET  | `/chat/models` | List available AI models | Bearer |

### Conversations (`/conversations`)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET  | `/conversations` | List conversations (cursor paginated) | Bearer |
| POST | `/conversations` | Create conversation | Bearer |
| GET  | `/conversations/{id}` | Get conversation with messages | Bearer |
| PATCH | `/conversations/{id}` | Update title, model, system prompt | Bearer |
| DELETE | `/conversations/{id}` | Delete conversation | Bearer |
| POST | `/conversations/{id}/messages` | Add message | Bearer |
| POST | `/conversations/{id}/summary` | Generate/summarize conversation | Bearer |

### Memory (`/memory`)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET  | `/memory` | List memories (filtered, paginated) | Bearer |
| POST | `/memory` | Create memory | Bearer |
| GET  | `/memory/{id}` | Get memory detail | Bearer |
| PATCH | `/memory/{id}` | Update memory | Bearer |
| DELETE | `/memory/{id}` | Delete memory | Bearer |
| POST | `/memory/search` | Semantic search with embeddings | Bearer |
| POST | `/memory/{id}/promote` | Promote short-term → long-term | Bearer |
| POST | `/memory/consolidate` | Trigger memory consolidation | Bearer |
| GET  | `/memory/stats` | Memory statistics | Bearer |

### Search (`/search`)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/search` | Execute search (Tavily) | Bearer |
| POST | `/search/deep` | Deep research mode | Bearer |
| GET  | `/search/history` | Search history | Bearer |
| DELETE | `/search/history/{id}` | Delete search history entry | Bearer |

### Files (`/files`)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/files/upload` | Upload file (multipart) | Bearer |
| GET  | `/files` | List files | Bearer |
| GET  | `/files/{id}` | Get file metadata | Bearer |
| GET  | `/files/{id}/download` | Download file | Bearer |
| DELETE | `/files/{id}` | Delete file | Bearer |
| POST | `/files/{id}/parse` | Parse file content (PDF, DOCX, etc.) | Bearer |
| POST | `/files/{id}/ocr` | OCR on image | Bearer |
| GET  | `/files/{id}/content` | Get parsed text content | Bearer |

### Plugins (`/plugins`)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET  | `/plugins` | List installed plugins | Bearer |
| GET  | `/plugins/marketplace` | List available plugins | Bearer |
| POST | `/plugins/install` | Install plugin | Bearer |
| POST | `/plugins/{name}/uninstall` | Uninstall plugin | Bearer |
| POST | `/plugins/{name}/configure` | Configure plugin | Bearer |
| GET  | `/plugins/{name}/status` | Plugin status | Bearer |
| POST | `/tools/execute` | Execute tool call | Bearer |

### Models (`/models`)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET  | `/models` | List available models | Bearer |
| GET  | `/models/{provider}` | List models for provider | Bearer |
| GET  | `/models/{provider}/{model}` | Model details | Bearer |

### Settings (`/settings`)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET  | `/settings` | Get all settings | Bearer |
| PATCH | `/settings` | Update settings | Bearer |
| GET  | `/settings/{key}` | Get specific setting | Bearer |

### Voice (`/voice`)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/voice/stt` | Speech-to-text (audio → text) | Bearer |
| POST | `/voice/tts` | Text-to-speech (text → audio) | Bearer |
| WS   | `/voice/ws` | WebSocket voice session | Bearer |
| POST | `/voice/session/create` | Create voice session | Bearer |
| POST | `/voice/session/{id}/process` | Process audio in session | Bearer |
| DELETE | `/voice/session/{id}` | Close session | Bearer |
| GET  | `/voice/sessions` | List active sessions | Bearer |

### Sync (`/sync`)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/sync/pull` | Pull changes since last sync | Bearer |
| POST | `/sync/push` | Push local changes | Bearer |
| POST | `/sync/status` | Get sync status | Bearer |
| POST | `/sync/resolve` | Resolve sync conflicts | Bearer |

### WebSocket (`/ws`)

| Path | Description | Auth |
|------|-------------|------|
| `/ws/events` | Real-time events (notifications, sync) | Bearer (query param) |
| `/ws/voice` | Voice session | Bearer (query param) |

## OpenAPI Specification

The canonical API definition lives at:

```
api/openapi.yaml
```

This file is the single source of truth. All client SDKs are generated from it. Changes to the API MUST be made to this file first (contract-first development), then implemented in the backend.

## Client SDK Generation

### Command

```bash
openapi-generator generate \
  -i api/openapi.yaml \
  -g kotlin \
  -o clients/kotlin \
  --additional-properties=library=retrofit2,useCoroutines=true

openapi-generator generate \
  -i api/openapi.yaml \
  -g swift \
  -o clients/swift \
  --additional-properties=library=urlsession

openapi-generator generate \
  -i api/openapi.yaml \
  -g typescript-axios \
  -o clients/typescript
```

### Generated SDK Structure

```
clients/kotlin/
├── src/
│   ├── main/kotlin/com/ultron/api/
│   │   ├── apis/          ← Generated API interfaces
│   │   ├── models/        ← Generated DTOs
│   │   ├── infrastructure/← Auth interceptors, serializers
│   │   └── UltronApi.kt  ← Unified client entry point
│   └── build.gradle.kts  ← Publishes as Maven artifact
```

The Android app depends on this SDK artifact, replacing the manual `ApiService.kt` DTOs.
