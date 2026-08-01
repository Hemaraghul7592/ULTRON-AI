# ULTRON Architecture — Complete Engineering Reference

## 1. Executive Summary

ULTRON is a multi-platform Personal AI Operating Companion with three active platforms:

- **Backend** (Python/FastAPI) — 20,591 lines across ~134 source files. Production-grade REST API.
- **macOS Desktop** (Swift 6) — 4,456 lines across 30 source files. Native Cocoa app.
- **Android Mobile** (Kotlin/Compose) — 3,039 lines across ~44 source files. Material 3 app.

The architecture follows a **Brain-Centric** design where a central orchestrator coordinates specialized engines. Engines are independently testable modules with single-entry-point services. The system has 7 completed backend engines (AI, Memory, Plugin, Search, File, Voice, Sync), an Agent System for orchestration, and a recently-completed macOS foundation with DI, Lifecycle, and Logging frameworks.

**Current test coverage**: 451 backend tests (pytest) + 156 macOS tests (Swift Testing) + Android instrumentation tests.

---

## 2. Folder Structure

```
ULTRON-AI/
├── backend/                    # Python/FastAPI backend (135+ source files)
│   ├── app/
│   │   ├── agent/              # Agent System — planner, executor, context
│   │   ├── ai/                 # AI Engine — providers, router, tool executor
│   │   ├── api/v1/             # REST API — auth, chat, memory, tools, voice, sync
│   │   ├── automation/         # Scheduler, reminders, background workers
│   │   ├── core/               # Config, database, encryption, logging, security
│   │   ├── file_engine/        # File storage, processors (text/image/pdf/audio/ocr)
│   │   ├── memory/             # Memory engine, embeddings, knowledge graph
│   │   ├── middleware/          # Error handler, rate limit, request ID, logging
│   │   ├── models/             # SQLAlchemy models (9 tables)
│   │   ├── observability/      # Dashboard, metrics
│   │   ├── plugins/            # Plugin system (10 plugins, 20 tools)
│   │   ├── repositories/       # Data access layer (9 repos)
│   │   ├── schemas/            # Pydantic models
│   │   ├── search/             # Search engine (Tavily provider)
│   │   ├── services/           # Auth, chat, Google OAuth
│   │   ├── sync/               # Sync engine — manager, resolver, queue
│   │   ├── tools/              # Tool router, plugin loader infrastructure
│   │   └── voice/              # Voice engine — STT/TTS providers
│   ├── alembic/                # Database migrations (5 revisions)
│   ├── tests/                  # 16 test files, 451 tests
│   └── scripts/                # Backup/restore
│
├── macos/                      # macOS Swift desktop (30 source files)
│   ├── Sources/ULTRON/
│   │   ├── ULTRONApp.swift     # @main entry point
│   │   ├── AppDelegate.swift   # NSApplicationDelegate lifecycle
│   │   └── Core/
│   │       ├── Configuration/  # Build config, runtime config, constants
│   │       ├── DI/             # Dependency container (11 files)
│   │       ├── Lifecycle/      # Startup phases, hooks, sequences
│   │       ├── Logging/        # Structured logging (9 files)
│   │       └── Orchestration/  # Proposed — not yet implemented
│   ├── Tests/                  # 5 test files, 156 tests
│   └── Configuration/          # 4 xcconfig build files
│
├── android/                    # Android Jetpack Compose (44 source files)
│   ├── app/src/main/java/com/ultron/
│   │   ├── core/               # Icons
│   │   ├── data/local/         # Room DB, DataStore
│   │   ├── data/remote/        # Retrofit API service
│   │   ├── data/repository/    # Chat + Memory repos
│   │   ├── di/                 # Hilt module
│   │   ├── domain/model/       # Domain models
│   │   └── ui/                 # 7 screens, navigation, theme
│   └── app/src/main/res/       # Resources
│
└── docs/                        # 14 architecture docs
```

---

## 3. System Architecture

### Backend Architecture

```
HTTP Request
    │
    ▼
┌──────────────────────────────────┐
│            Middleware             │
│ Security → RequestID → RateLimit │
│ → RequestLogger → ErrorHandler   │
└────────────┬─────────────────────┘
             │
             ▼
┌──────────────────────────────────┐
│          API Router              │
│ /auth /chat /memory /tools      │
│ /voice /sync /observability     │
└────────────┬─────────────────────┘
             │
    ┌────────┴──────────┐
    ▼                   ▼
┌─────────┐        ┌──────────┐
│ Services│        │  Agent   │
│ Auth    │        │  System  │
│ Chat    │        │ Planner  │
│ OAuth   │        │ Executor │
└────┬────┘        └────┬─────┘
     │                  │
     └──────┬───────────┘
            ▼
┌────────────────────────────────────┐
│          Engine Layer              │
│  AI  │ Memory │ Search │ File     │
│  Voice │ Sync │ Plugin │ Agent   │
└────────────┬───────────────────────┘
             │
             ▼
┌────────────────────────────────────┐
│         Data Layer                 │
│  Repositories → SQLAlchemy → DB   │
└────────────────────────────────────┘
```

### macOS Architecture

```
ULTRONApp (@main)
    │
    ▼
AppDelegate (@MainActor, NSApplicationDelegate)
    │
    ├── StartupSequence (6 phases, typed enum)
    │
    ├── DependencyContainer (@MainActor)
    │   ├── register / _resolveCore / cycle detection
    │   └── ContainerDiagnostics (validate, graph, stats)
    │
    ├── Logger (actor)
    │   └── ConsoleDestination / FileDestination / CompositeDestination
    │
    └── LifecycleHooks (future: orchestration, network, AI)
```

---

## 4. Dependency Injection (macOS)

### Architecture

The macOS DI system is a custom, zero-dependency, `@MainActor`-based container.

```
Registration          Resolution
    │                     │
register(Type, lifetime)  _resolve(Type)
    │                     │
    ▼                     ▼
ServiceRegistration   look up ObjectIdentifier
(immutable)           │
    │                  ├── singleton cache?
    ▼                  ├── beginResolution (cycle detect)
ServiceRecord         ├── executeFactory
(mutable runtime)     ├── cacheIfSingleton
                      └── return
```

### Key Types

| Type | Purpose |
|------|---------|
| `DependencyContainer` | @MainActor class. Register, resolve, validate. |
| `ServiceRegistration` | Immutable: type, lifetime, factory, typeName. |
| `ServiceRecord` | Runtime: registration + index + cachedInstance. |
| `RegistrationSnapshot` | Public metadata: typeName, lifetime, index. |
| `ResolutionFrame` | Stack frame for cycle detection. |
| `ContainerDiagnostics` | Read-only: validate(), dependencyGraph(), registeredTypes(). |
| `ContainerError` | .notRegistered, .circularDependency, .factoryFailed. |

### Lifetime

- `singleton` — Created once, cached forever.
- `transient` — Created fresh on every resolve.
- `scoped` — Reserved for future.

### Singletons (FROZEN)

`_resolveCore(for: ObjectIdentifier)` is the single canonical pipeline. 4 callers, 0 duplication.

---

## 5. Lifecycle (macOS)

### StartupSequence

```
configuration (0) → logging (100) → dependencyInjection (200)
→ applicationState (300) → windowSystem (400) → ready (500)
```

`StartupPhase` is a `CaseIterable` enum. Adding a phase = adding a case.

### ShutdownSequence

Reverse phase order. Fire-and-forget. Every hook executes.

### LifecycleHook Protocol

```swift
protocol LifecycleHook: Identifiable {
    var phase: StartupPhase { get }
    var priority: Int { get }        // default 0
    var label: String { get }
    func onStartup() async throws
    func onShutdown() async
}
```

### AppDelegate

- `applicationDidFinishLaunching()` → runs startup sequence, handles failures with NSAlert.
- `applicationShouldTerminate()` → returns `.terminateLater`, runs shutdown hooks, replies when complete.

---

## 6. Logging (macOS)

### Architecture

```
Logger (actor)
    │
    ├── LoggerConfiguration (minimumLevel, subsystem, destinations)
    │
    ├── LogEntry (timestamp, level, message, subsystem, metadata, source)
    │
    ├── LogDestination (protocol)
    │   ├── ConsoleDestination (os_log)
    │   ├── FileDestination (append to file)
    │   └── CompositeDestination (forwards to children)
    │
    └── LogEntryFormatter (protocol)
        ├── PlainTextFormatter (ISO8601 + level + subsystem)
        └── JSONFormatter (structured JSON)
```

### Features

- Actor-isolated for thread safety
- 5 levels: `.trace < .debug < .info < .warning < .error`
- `LogLevel` encodes as lowercase strings for JSON (`"error"`, not `4`)
- Automatic source location capture (#fileID, #function, #line)
- Filtering by minimum level
- Structured metadata as `[String: String]`

---

## 7. Configuration

### Backend (`app/core/config.py`)

Pydantic `Settings` with `.env` support. Key settings:

| Category | Keys |
|----------|------|
| AI | GROQ_API_KEY, GEMINI_API_KEY, OPENAI_API_KEY, GROK_API_KEY, DEFAULT_AI_PROVIDER |
| Plugins | GITHUB_TOKEN, TAVILY_API_KEY, OPEN_WEATHER_API_KEY, OCR_API_KEY, NOTION_API_KEY |
| Google | GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_MAPS_API_KEY |
| Security | SECRET_KEY, ENCRYPTION_KEY, ACCESS_TOKEN_EXPIRE_MINUTES |
| Voice | TTS_ENABLED, STT_ENABLED, TTS_MODEL, STT_MODEL |
| Memory | MEMORY_SHORT_TERM_MAX, MEMORY_LONG_TERM_THRESHOLD, EMBEDDING_DIM |

### macOS (`Core/Configuration/`)

| File | Purpose |
|------|---------|
| `BuildConfiguration.swift` | Compile-time: .development, .debug, .release, .production |
| `Configuration.swift` | Runtime: bundle, environment, version, isTesting |
| `Constants.swift` | Fixed: window sizes, animation durations, URLs, limits |

Build configs via 4 `.xcconfig` files: Development, Debug, Release, Production.

---

## 8. Providers (Backend)

### AI Providers (`app/ai/providers/`)

| Provider | Model | API |
|----------|-------|-----|
| OpenAI | gpt-4o-mini | api.openai.com/v1 |
| Groq | llama-3.3-70b-versatile | api.groq.com/openai/v1 |
| Grok | grok-2-latest | api.x.ai/v1 |
| Gemini | gemini-2.0-flash | generativelanguage.googleapis.com |

Architecture: `AIProvider` base class → `OpenAICompatibleProvider` → concrete providers. `AIProviderRouter` with fallback. `AIService` as single entry point.

### Voice Providers (`app/voice/providers/`)

| Provider | STT | TTS |
|----------|-----|-----|
| Groq | Whisper via Groq | playai-tts |
| Gemini | Gemini Flash | Gemini Flash TTS |
| Mock | Returns test data | Returns test audio |

### Plugin System (`app/plugins/`)

| Plugin | Tools | Auth |
|--------|-------|------|
| Weather | get_weather, get_weather_forecast | API key |
| Google Drive | search, read | OAuth |
| GitHub | list_repos, search, list_issues | Token |
| Notion | search, read_page | API key |
| OCR | ocr_extract_text, read_image | API key |
| Gmail | search, read_message | OAuth |
| Calendar | list_events, create_event | OAuth |
| Google Maps | geocode, search_places | API key |
| Tavily | search, answer | API key |
| People | search_contacts, get_profile | OAuth |

20 tools across 10 plugins. `PluginManager` centralizes registration, health, execution.

### Search Provider (`app/search/providers/`)

- `TavilyProvider` — wraps Tavily API with retry, error normalization, source extraction.

### Sync Provider (`app/sync/providers/`)

- `MockSyncProvider` — test provider. Future: GoogleDriveSyncProvider, DropboxSyncProvider.

### Storage Provider (`app/file_engine/storage/`)

- `LocalStorage` — filesystem with path traversal protection.

### File Processors (`app/file_engine/processors/`)

- TextProcessor, ImageProcessor, PDFProcessor, AudioProcessor, OCRProcessor (delegates to plugin engine).

---

## 9. Engines (Backend)

### AI Engine (`app/ai/`)

- `AIService` — single entry point for all AI operations.
- `AIProviderRouter` — manages multiple providers with automatic fallback.
- `ToolExecutor` — syncs from PluginManager, executes tool calls.
- `ContextBuilder`, `PromptBuilder` — construct prompts with memory, history, system prompt.

### Memory Engine (`app/memory/`)

- `MemoryService` — CRUD, search, context retrieval, archive/restore.
- `MemoryEngine` — semantic search, importance-based promotion, summarization.
- `EmbeddingService` — generates embeddings (sentence-transformers or hash fallback).
- `KnowledgeGraph` — entity extraction, relationship management.
- Categories: general, user_profile, preference, project, conversation.

### Plugin Engine (`app/plugins/`)

- `PluginManager` — wraps ToolRouter + PluginLoader with status tracking, health, error normalization.
- `PluginInterface` — enhanced BasePlugin with health_check(), validate(), permissions.
- 10 plugins providing 20 tools.

### Search Engine (`app/search/`)

- `SearchService` — caching, deduplication, citations, retry, timeout, research mode.
- `TavilyProvider` — wraps Tavily API.
- `SearchCache` — SHA-256 keyed, configurable TTL, hit/miss tracking.

### File Engine (`app/file_engine/`)

- `FileService` — save, load, delete, copy, move, extract_text, deduplication (SHA-256).
- `LocalStorage` — filesystem with path traversal protection.
- Processors: Text, Image (header parsing, no Pillow), PDF, Audio, OCR (delegates to Plugin Engine).

### Voice Engine (`app/voice/`)

- `VoiceService` — transcribe, synthesize, process (full pipeline), sessions.
- Providers: GroqSTT/TTS, GeminiSTT/TTS, MockSTT/TTS.
- Audio validation, format detection (WAV/MP3/OGG), duration estimation.

### Sync Engine (`app/sync/`)

- `SyncService` — push, pull, sync, track changes.
- `SyncManager` — coordinates providers, conflict resolver, queue.
- `ConflictResolver` — 4 strategies: last_write_wins, timestamp, provider_priority, manual.
- `SyncQueue` — retry with exponential backoff.

### Agent System (`app/agent/`)

- `AgentService` — orchestrates: Planner → TaskGraph → Executor.
- `Planner` — regex-based intent detection (search, memory, file, plugin, voice, sync).
- `Executor` — runs tasks respecting dependencies, retries, deadlock detection.
- `AgentContext` — propagates state across tasks, execution log.

---

## 10. Database (Backend)

### Models (9 tables)

| Table | Purpose |
|-------|---------|
| `users` | Authentication, profiles |
| `conversations` | Chat conversation metadata |
| `messages` | Individual chat messages with role, model, tool_calls |
| `memories` | Long-term memory with type, category, archive, importance |
| `tags` + `memory_tags` | Many-to-many memory tagging |
| `tasks` + `jobs` | Task management with recurring cron support |
| `token_usage` | AI token consumption tracking per provider/model |
| `entities` + `relationships` | Knowledge graph storage |
| `google_tokens` | Encrypted OAuth refresh tokens |
| `metrics` | Application observability metrics |

### Database Support

- SQLite (default, `aiosqlite`)
- PostgreSQL (production, `asyncpg`)
- Auto-detection: `is_postgres` property on Settings

### Migrations (Alembic)

5 revisions: initial schema, user_id columns, token_usage user_id, google_tokens, memory category/archive.

### Repositories

9 repositories follow a consistent async pattern: `AsyncSession` injection, standard CRUD, user-scoped queries. `escape_like()` utility for LIKE escaping.

---

## 11. API (Backend)

### Routers — 10 under `/api/v1/`

| Router | Prefix | Endpoints | Auth |
|--------|--------|-----------|------|
| auth | `/auth` | register, login, token refresh | Public |
| chat | `/chat` | chat (SSE streaming), chat_stream | Bearer |
| conversations | `/conversations` | CRUD, list, message history | Bearer |
| memory | `/memory` | CRUD, search, archive, stats, categories | Bearer |
| tasks | `/tasks` | CRUD, list, complete | Bearer |
| entities | `/entities` | CRUD, relationships | Bearer |
| google_auth | `/google/auth` | OAuth login, callback, status, disconnect | Bearer |
| voice | `/voice` | STT, TTS, session create/process/close | Bearer |
| tools | `/tools` | List, execute, plugins, health, status | Bearer |
| observability | `/observability` | Metrics, dashboard | Bearer |

### Authentication

JWT-based with `python-jose`. HS256 algorithm. Token expires in 1440 minutes (configurable). `verify_token` dependency on protected routes.

### Google OAuth2

Full OAuth2 flow: authorization URL → callback → token exchange → encrypted storage. Refresh token auto-refresh. Scopes per service (drive, gmail, calendar, people).

### Middleware Stack

`SecurityHeaders → RequestID → RateLimit → RequestLogger → ErrorHandler`

---

## 12. Testing

### Backend (pytest)

| File | Tests | Coverage |
|------|-------|----------|
| `test_memory.py` | 55 | Service, repository, categories, archive, API |
| `test_ai_providers.py` | 46 | Providers, errors, streaming, fallback |
| `test_plugins.py` | 41 | Interface, errors, manager, executor |
| `test_agent.py` | 45 | Planner, executor, service, integration |
| `test_sync.py` | 60 | Provider, manager, service, queue, resolver |
| `test_search.py` | 48 | Provider, service, cache, integration |
| `test_voice.py` | 45 | Provider, service, session, validation |
| `test_file_engine.py` | 56 | Storage, processors, service, models |
| `test_h5.py` | 25 | Integration: auth, conversation, voice API |
| `test_api.py` | 12 | Health, root, conversations |
| `test_auth.py` | ~10 | Registration, login |
| `test_automation.py` | ~8 | Tasks, scheduler |
| `test_core.py` | ~8 | Config, health, rate limiting |
| `test_ai.py` | 11 | Prompt builder, context builder |

**Total**: 451 tests. Framework: `pytest` + `pytest-asyncio` (auto mode). Conftest: SQLite in-memory, auto-drop tables.

### macOS (Swift Testing)

| File | Tests | Coverage |
|------|-------|----------|
| `DependencyContainerTests.swift` | 54 | Registration, resolution, cycles |
| `ContainerDiagnosticsTests.swift` | 28 | Validate, types, graph, stats |
| `LoggerTests.swift` | 28 | Levels, entries, formatters, destinations, concurrency |
| `LifecycleTests.swift` | 35 | Phases, ordering, hooks, shutdown |
| `ConfigurationTests.swift` | 22 | Build config, runtime, constants |

**Total**: 167 tests. Framework: Swift Testing (`@Test`, `#expect`).

### Android

JUnit + MockK + Turbine + Espresso for UI tests.

### Test Patterns

- **Protocol-based mocking**: Every dependency behind a protocol. Mock implementations in tests.
- **In-memory databases**: Backend uses `aiosqlite` with auto-create/drop per test.
- **DI container with test overrides**: macOS `register()` overwrites allow test-specific configurations.
- **@MainActor test suites**: Swift 6 concurrency-safe test isolation.

---

## 13. Coding Standards

### Backend (Python)

- Ruff linter with strict ruleset
- mypy strict mode
- `structlog` for structured logging
- Pydantic v2 for validation
- SQLAlchemy 2.0 async sessions
- `from __future__ import annotations` everywhere
- Module-level `get_logger(__name__)`
- Test file naming: `test_<module>.py`

### macOS (Swift)

- Swift 6 with strict concurrency checking
- `@MainActor` for all UI-related types
- Actors for shared mutable state
- Structs by default; classes only for reference semantics
- Protocols for all abstractions
- No `@unchecked Sendable`
- No force unwrapping in production code
- `// MARK: -` section organization
- Documentation on every public type

---

## 14. Existing Strengths

1. **Single-entry-point pattern** — Every engine has one public API (XxxService). Internal complexity is hidden.
2. **Provider abstraction** — AI models, search backends, STT/TTS, storage — all behind protocols. Swappable without callers knowing.
3. **Custom DI (macOS)** — 806 lines, zero dependencies. Production-hardened with cycle detection, diagnostics, and validation.
4. **Typed startup phases (macOS)** — `StartupPhase` enum eliminates magic numbers. Adding a phase = adding a case.
5. **Structured logging (macOS)** — Actor-isolated. Multiple destinations. Plain text + JSON formatters.
6. **Comprehensive testing** — 451 backend tests + 156 macOS tests. Protocol-based mocking.
7. **Security-first design** — Keychain for secrets (macOS), Fernet encryption for OAuth tokens (backend), path traversal protection.
8. **Alembic migrations** — 5 tracked revisions, forward and reverse migrations.
9. **Docker support** — Multi-stage Python build, docker-compose with PostgreSQL + Redis.
10. **Cross-platform** — Shared architecture patterns across Python, Swift, and Kotlin.

---

## 15. Weaknesses

1. **No universal orchestration layer** — The backend has multiple parallel orchestration systems (PluginManager, SearchService, VoiceService, SyncService). The macOS app has none yet. A universal `ServiceOrchestrator<P>` pattern would unify them.

2. **AI provider switching is primitive** — `AIProviderRouter` uses sequential fallback with no circuit breakers, health monitoring, or cooldown periods. Failures are retried immediately with no backoff.

3. **No retry framework** — Retry logic is duplicated across `TavilyProvider`, voice providers, and the sync queue. Each implements its own retry with different semantics.

4. **Backend logging lacks structured levels** — Uses `structlog` but log levels aren't consistently enforced as a filter. No per-subsystem minimum level configuration.

5. **No caching layer** — Only the SearchEngine has a cache. Memory, AI responses, and API calls have no caching. Repeated calls hit external APIs.

6. **File engine processes are synchronous** — Image/PDF parsing happens on the main async path. Large files could block the event loop.

7. **Plugins have direct API access** — Plugins create their own `httpx` clients. There's no central HTTP client with retry, circuit breaking, or telemetry.

8. **No RateLimiter for AI providers** — Token usage tracking exists but doesn't enforce limits. Could exhaust quotas.

9. **macOS has no networking layer** — The `APIClient`, `WebSocketClient`, and `SyncEngine` are designed but not implemented.

10. **Configuration is file-based** — No remote configuration. Adding a new provider requires editing code or `.env`.

---

## 16. Future Roadmap

### Immediate Priority (macOS completion)

- PR #5: Universal Service Orchestrator (retry, failover, circuit breaker, health)
- PR #6: Networking layer (APIClient, WebSocket, backend integration)
- PR #7: Window Management (overlay, settings, menu bar)

### Medium Priority (Backend hardening)

- PR #8: Universal orchestrator for backend AI/search/voice providers
- PR #9: Central caching layer (Redis-based, swappable)
- PR #10: Enhanced observability (prometheus metrics, distributed tracing)

### Phase 3 Completion

- macOS desktop functional with backend integration
- AI model switching via orchestrator
- Voice pipeline on macOS
- File management on macOS

### Phase 4+ (Future)

- iPhone/iPad companion app (SwiftUI reuse)
- Local LLM support (MLX on macOS)
- Multi-device sync via backend
- Plugin marketplace
- Team collaboration features
