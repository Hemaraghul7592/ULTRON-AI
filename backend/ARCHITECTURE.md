# Architecture

## Overview

ULTRON is a modular FastAPI backend with async SQLAlchemy, structured into:

```
app/
  ai/            — AI provider routing & context building
  api/v1/        — REST endpoints (auth, chat, conversations, memory, etc.)
  automation/    — Scheduler, reminders, background worker
  core/          — Config, database, health, logging, security, rate limiter
  jobs/          — Background job definitions
  memory/        — Memory engine, entity extraction
  middleware/     — Request ID, rate limiting, error handling, security headers
  models/        — SQLAlchemy ORM models
  observability/ — Metrics, dashboard service
  plugins/       — Plugin system
  repositories/  — Data access layer
  schemas/       — Pydantic request/response schemas
  services/      — Business logic (auth, chat, oauth)
  tools/         — Tool execution, plugin loader, router
  voice/         — STT/TTS pipeline, session management
```

## Key Patterns

### Dependency Injection

Services receive dependencies via FastAPI `Depends()`. Singletons (tool router, voice pipeline, session manager) are stored in `app.state` via the lifespan handler.

### Repository Pattern

All database access goes through repository classes. Repositories accept `AsyncSession` and return ORM models. This keeps business logic testable without touching the database.

### User Isolation

Every query is scoped by `user_id` extracted from the JWT. The `verify_token` dependency decodes the JWT and returns `{"user_id": ..., "sub": ..., "role": ...}`.

### Graceful Degradation

Redis is optional. If `REDIS_URL` is not configured or Redis is unavailable, the system falls back to in-memory rate limiting.

## Data Flow

```
Client → FastAPI → Middleware (Request ID → Rate Limit → Logger → Error Handler) → Router → Service → Repository → Database
```

## Database

- SQLite for development
- PostgreSQL for production
- Alembic for migrations
- Async drivers: `aiosqlite` / `asyncpg`
