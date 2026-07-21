# API Reference

## Public Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/` | Root info |
| GET | `/health` | Health check (DB + Redis) |
| GET | `/livez` | Liveness probe |
| GET | `/readyz` | Readiness probe |

## Authentication

All other endpoints require `Authorization: Bearer <token>` header.

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/auth/register` | Register a new user |
| POST | `/api/v1/auth/login` | Login |
| GET | `/api/v1/auth/verify` | Verify token |

## Conversations

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/conversations` | List conversations |
| POST | `/api/v1/conversations` | Create conversation |
| GET | `/api/v1/conversations/{id}` | Get conversation |
| PATCH | `/api/v1/conversations/{id}` | Update conversation |
| DELETE | `/api/v1/conversations/{id}` | Delete conversation |
| POST | `/api/v1/conversations/{id}/messages` | Add message |

## Chat

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/chat` | Send message (non-streaming) |
| POST | `/api/v1/chat/stream` | Send message (streaming) |

## Memory

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/memory` | List memories |
| POST | `/api/v1/memory` | Create memory |
| GET | `/api/v1/memory/{id}` | Get memory |
| DELETE | `/api/v1/memory/{id}` | Delete memory |
| POST | `/api/v1/memory/search` | Search memories |

## Tasks

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/tasks` | List tasks |
| POST | `/api/v1/tasks` | Create task |
| GET | `/api/v1/tasks/{id}` | Get task |
| PATCH | `/api/v1/tasks/{id}` | Update task |
| DELETE | `/api/v1/tasks/{id}` | Delete task |

## Entities

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/entities` | List entities |
| POST | `/api/v1/entities` | Create entity |
| GET | `/api/v1/entities/{id}` | Get entity |

## Voice

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/voice/stt` | Speech-to-text |
| POST | `/api/v1/voice/tts` | Text-to-speech |
| POST | `/api/v1/voice/session/create` | Create voice session |
| POST | `/api/v1/voice/session/{id}/process` | Process audio input |
| POST | `/api/v1/voice/session/{id}/process-text` | Process text input |
| DELETE | `/api/v1/voice/session/{id}` | Close session |
| GET | `/api/v1/voice/sessions` | List active sessions |

## Tools

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/tools` | List tools |
| GET | `/api/v1/tools/definitions` | Get tool definitions |
| POST | `/api/v1/tools/execute` | Execute a tool |
| GET | `/api/v1/tools/plugins` | List plugins |

## Observability

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/observability/dashboard` | Dashboard data |
| GET | `/api/v1/observability/metrics` | Recent metrics |
| GET | `/api/v1/observability/metrics/latency` | Latency percentiles |
| GET | `/api/v1/observability/metrics/tokens` | Token usage |
