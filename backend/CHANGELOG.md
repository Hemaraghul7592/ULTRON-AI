# Changelog

## H6 — Production Readiness & Release (2026-07-20)

### Added
- GitHub Actions CI: ruff, mypy, pytest, alembic migration verification, Docker build
- Multi-stage Dockerfile with slim production image, non-root `ultron` user, healthcheck
- `.dockerignore` for minimal Docker context
- Liveness (`/livez`) and readiness (`/readyz`) endpoints
- Security headers middleware (X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, Referrer-Policy)
- Backup and restore scripts (`scripts/backup.sh`, `scripts/restore.sh`)
- `.gitignore` for generated files and IDE artifacts
- `ARCHITECTURE.md`, `DEPLOYMENT.md`, `API.md`, `TROUBLESHOOTING.md` documentation
- `libpq-dev` in Dockerfile for asyncpg PostgreSQL driver

### Changed
- `.env.example` updated with all environment variables documented
- Removed duplicate `/health` endpoint from observability router
- Removed stale `set_tool_router()` global and `MessageCount` type alias
- Removed unused `import time` from health.py, unused imports from voice.py
- `pyproject.toml` ruff config: per-file-ignores for test files (S101, S105, SLF001)

### Fixed
- Alembic migration chain: `3c4d5e6f7g8h` now correctly references `7496ccf83cb6`
- Unused variable `conv_id` in test_h5.py

### Infrastructure
- `.github/workflows/ci.yml` — 5 job CI pipeline
- Docker Compose with PostgreSQL and Redis services (enabled by default)
- Environment variable validation on startup (SECRET_KEY, ENCRYPTION_KEY)

## H5 — Health, Performance & Production Readiness (2026-07-20)

### Added
- Enhanced health endpoint with DB connectivity check (`SELECT 1`) and Redis ping
- `user_id` column on `TokenUsage` model for per-user token tracking
- Alembic migration `3c4d5e6f7g8h` for `token_usage.user_id`
- Batch message count query to eliminate N+1 in conversation listing
- PostgreSQL service in docker-compose.yml (with healthcheck)
- Redis service in docker-compose.yml (with healthcheck)
- Comprehensive tests: health checks, voice sessions, tool endpoints, user isolation, error paths

### Changed
- Health endpoint now reports DB and Redis status with `checks` object
- `VoiceSessionManager` and `VoicePipeline` moved from global singletons to FastAPI `app.state`
- `ToolRouter` accessible via `app.state` with fallback to global singleton
- `TokenRepository.record()` accepts `user_id` parameter
- `ChatService` passes `user_id` to token usage tracking
- `ConversationRepository.list_all()` no longer eagerly loads messages (eliminates N+1)
- `ConversationRepository.get_message_counts()` added for batch message count queries
- `docker-compose.yml` enables PostgreSQL and Redis services
- `get_engine()` added to `app.core.database` for health checks

### Migration
- New revision: `3c4d5e6f7g8h` (adds `user_id` to token_usage)

## H4 — Infrastructure & Multi-Tenancy (2026-07-20)

### Added
- Redis-backed rate limiter with graceful in-memory fallback
- Stricter rate limits for auth endpoints (10/min vs 60/min)
- Request ID middleware — UUID per request via `X-Request-ID` header
- Standardized error response format: `error_code`, `message`, `request_id`, optional `details`
- Log sanitization — redacts passwords, tokens, API keys, auth headers, secrets
- User-scoped data access — all queries filtered by `user_id` from JWT
- `user_id` column on `Conversation`, `Memory`, `Task`, `Entity` models

### Changed
- `InMemoryRateLimiter` replaces old `RateLimiter` class
- JWT tokens now include `user_id` claim
- `verify_token` returns `user_id`; routers pass it to repositories
- `MemoryEngine`, `KnowledgeGraphService`, `ChatService` accept `user_id`
- Replaced deprecated `@app.on_event("startup")`/`@app.on_event("shutdown")` with FastAPI `lifespan` handler

### Fixed
- Removed duplicate index definitions in model `__table_args__` (already implied by `index=True` on column)
- Alembic migration uses `batch_alter_table` for SQLite compatibility
- `REDIS_URL` setting added (empty = in-memory fallback only)

### Migration
- New revision: `7496ccf83cb6` (adds `user_id` to conversations, memories, tasks, entities)

## H3 — Production Hardening

### Added
- SECRET_KEY validation with clear error message
- .gitignore for generated files
- Alembic migration for initial schema
- LIKE escaping in search queries
- Password complexity validation (uppercase, lowercase, digit, special char)
- Voice file size limits

### Changed
- Production-quality review of all modules
