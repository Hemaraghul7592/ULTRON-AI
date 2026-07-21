# Changelog

## [1.0.3] - 2026-07-20

### Phase C — Production Hardening

#### Backend
- **H3A**: Rejected insecure default SECRET_KEY at startup with clear error message and `openssl rand -hex 32` hint (`app/core/config.py`). Created production `.gitignore` (`.env`, `*.db`, `__pycache__`, `.pytest_cache`, `.venv`, build artifacts, IDE files, OS files, logs). Pinned `bcrypt<4.1` for `passlib` compatibility (`pyproject.toml`). Updated test environment to set `SECRET_KEY` and `ENCRYPTION_KEY` via `conftest.py`.
- **H3B**: Gated `Base.metadata.create_all` behind `settings.DEBUG` — never runs in production (`app/main.py`). Configured Alembic with dynamic `DATABASE_URL` from settings (`alembic/env.py`). Generated and committed initial migration (`alembic/versions/1ba6700f8cd2_initial_schema.py`).
- **H3C**: Escaped SQL LIKE wildcards (`%`, `_`, `\`) in `MemoryRepository` and `EntityRepository` queries. Extracted shared `escape_like()` utility to `app/repositories/utils.py` (`app/repositories/memory_repo.py`, `app/repositories/entity_repo.py`).
- **H3D**: Added password complexity enforcement to `UserCreate` schema: minimum 8 characters, uppercase, lowercase, digit, and special character with clear validation errors (`app/schemas/auth.py`).
- **H3E**: Added request body size limits for voice/audio endpoints — 25MB raw, 35MB base64 (`app/schemas/voice.py`).

## [1.0.2] - 2026-07-20

### Phase B — Authentication & Password Security

#### Backend
- **H1**: Protected all API endpoints with router-level `dependencies=[Depends(verify_token)]`. Public routes: `/`, `/health`, `/auth/*`, `/docs`, `/redoc`, `/openapi.json` (DEBUG-gated). Added `AuthenticationException` -> 401 mapping in error handler middleware.
- **H2**: Replaced in-memory `_MASTER_PASSWORD_HASH` with database-persisted password hashing. Created `User` model (`app/models/user.py`), `UserRepository` (`app/repositories/user_repo.py`), `AuthService` (`app/services/auth_service.py`). Added `/auth/register` endpoint. Removed restart bypass (auto-token when no password set). Tables auto-created on startup.

## [1.0.1] - 2026-07-20

### Phase A — Critical Security & Auth Fixes

#### Backend
- **C1**: Replaced insecure `client_id`-as-Bearer-token with proper Google OAuth2 token exchange via `GoogleOAuthService` (`app/services/google_oauth.py`). Updated Drive, Gmail, and Calendar plugins to use OAuth2 refresh token flow.
- **C2**: Moved Gemini API key from URL query parameter to `x-goog-api-key` header in `ai/provider.py`, `voice/stt.py`, and `voice/tts.py`.
- **C3**: Made `ENCRYPTION_KEY` a mandatory setting — startup now fails with a clear error message if it is missing, instead of silently falling back to `SECRET_KEY`.
- **C4**: Deleted stale duplicate `Project/` directory.

## [1.0.0] - 2026-07-19

### Initial Release

#### Backend
- **Architecture**: FastAPI + SQLAlchemy + Pydantic + Alembic
- **AI Core**: Groq and Gemini providers with fallback routing
- **Streaming**: Server-sent events for real-time chat responses
- **Tool Calling**: Function calling with multi-round tool execution
- **Memory Engine**: Short-term, long-term, episodic memory with embeddings
- **Knowledge Graph**: Entity extraction and relationship tracking
- **Voice Pipeline**: STT (Whisper) and TTS (PlayAI/Gemini)
- **Tools & Plugins**: Weather, Google Drive, GitHub, Notion, OCR, Gmail, Calendar
- **Automation**: Scheduler, reminder engine, background workers
- **Security**: Encrypted tokens, JWT auth, rate limiting
- **Observability**: Metrics, latency tracking, dashboard API
- **Database**: SQLite with PostgreSQL-ready architecture

#### Android
- **UI**: Jetpack Compose with Material 3
- **Architecture**: MVVM with Clean Architecture
- **DI**: Hilt dependency injection
- **Local DB**: Room for offline storage
- **Networking**: Retrofit + OkHttp
- **Settings**: DataStore preferences
- **Screens**: Splash, Onboarding, Chat, Voice, Memory, Settings, Dashboard
- **Navigation**: Bottom navigation with Compose Navigation
- **Dark Mode**: Full dark mode support
- **Animations**: Smooth transitions and state animations

#### Testing
- **API Tests**: End-to-end endpoint testing
- **Core Tests**: Security, encryption, rate limiting
- **AI Tests**: Prompt builder, context builder
- **Memory Tests**: Entity extraction, memory classification
- **Automation Tests**: Scheduler, reminders, background workers

#### Infrastructure
- **Docker**: Production-ready Dockerfile and docker-compose
- **Alembic**: Database migration support
- **CI/CD**: Ready for GitHub Actions

### Files Created

#### Backend (Python/FastAPI)
- `backend/pyproject.toml` - Project configuration
- `backend/app/core/config.py` - Settings management
- `backend/app/core/database.py` - Database engine and sessions
- `backend/app/core/security.py` - JWT and password hashing
- `backend/app/core/encryption.py` - Fernet encryption
- `backend/app/core/exceptions.py` - Custom exceptions
- `backend/app/core/logging.py` - Structured logging
- `backend/app/core/rate_limiter.py` - Rate limiting
- `backend/app/models/` - SQLAlchemy models (Conversation, Message, Memory, Tag, Task, Job, Entity, Relationship, TokenUsage, Metric)
- `backend/app/schemas/` - Pydantic schemas for all models
- `backend/app/repositories/` - Repository pattern data access
- `backend/app/ai/` - AI provider interface, Groq/Gemini providers, router, prompt builder, context builder, tool executor
- `backend/app/memory/` - Memory engine, embeddings, knowledge graph, entity extractor
- `backend/app/voice/` - STT, TTS, voice pipeline, session manager
- `backend/app/tools/` - Tool router, plugin loader, base classes
- `backend/app/plugins/` - Weather, Google Drive, GitHub, Notion, OCR, Gmail, Calendar plugins
- `backend/app/automation/` - Scheduler, reminders, background workers
- `backend/app/observability/` - Metrics service, dashboard
- `backend/app/services/chat_service.py` - Main chat orchestrator
- `backend/app/middleware/` - Error handling, request logging, rate limiting
- `backend/app/api/v1/` - All API endpoints (chat, conversations, memory, tasks, entities, voice, tools, observability, auth)
- `backend/app/main.py` - FastAPI application
- `backend/alembic/` - Migration configuration
- `backend/tests/` - Test suite

#### Android (Kotlin/Jetpack Compose)
- `android/build.gradle.kts` - Root build config
- `android/app/build.gradle.kts` - App build config with all dependencies
- `android/app/src/main/AndroidManifest.xml` - App manifest
- `android/app/src/main/java/com/ultron/UltronApp.kt` - Application class
- `android/app/src/main/java/com/ultron/di/AppModule.kt` - Hilt DI module
- `android/app/src/main/java/com/ultron/data/local/` - Room database, DAOs, entities, DataStore
- `android/app/src/main/java/com/ultron/data/remote/ApiService.kt` - Retrofit API interface
- `android/app/src/main/java/com/ultron/data/repository/` - Repository implementations
- `android/app/src/main/java/com/ultron/domain/model/Models.kt` - Domain models
- `android/app/src/main/java/com/ultron/ui/theme/` - Material 3 theme
- `android/app/src/main/java/com/ultron/ui/navigation/Navigation.kt` - Navigation config
- `android/app/src/main/java/com/ultron/ui/components/ChatBubble.kt` - Chat UI components
- `android/app/src/main/java/com/ultron/ui/screens/` - All screens (Splash, Onboarding, Chat, Memory, Voice, Settings, Dashboard)
- `android/app/src/main/java/com/ultron/ui/MainActivity.kt` - Main activity with navigation
