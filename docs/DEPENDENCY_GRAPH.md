# ULTRON — Dependency Graph

## Module Dependency Graph (Backend)

```
main.py
    │
    ├── app/agent/ ─────────────────────────────┐
    │   ├── service.py ──→ models.py, planner.py │
    │   ├── planner.py ──→ models.py              │
    │   ├── executor.py ──→ context.py, errors.py │
    │   └── context.py ──→ models.py              │
    │                                             │
    ├── app/ai/ ───────────────┐                 │
    │   ├── service.py ──→ provider.py, router.py │
    │   ├── router.py ──→ providers/             │
    │   └── tool_executor.py ──→ plugins/manager  │
    │                                             │
    ├── app/api/v1/ ─────────────────────────────┤
    │   ├── chat.py ──→ services/chat_service     │
    │   ├── auth.py ──→ services/auth_service     │
    │   ├── memory.py ──→ memory/service          │
    │   ├── tools.py ──→ plugins/manager          │
    │   ├── voice.py ──→ voice/service            │
    │   └── google_auth.py ──→ services/google_oauth│
    │                                             │
    ├── app/services/ ────────────────────────────┤
    │   ├── chat_service.py ──→ ai/, memory/, agent/│
    │   └── google_oauth.py ──→ repositories/      │
    │                                             │
    ├── app/memory/ ──────────────────────────────┤
    │   ├── service.py ──→ engine, repositories   │
    │   └── engine.py ──→ embeddings, knowledge    │
    │                                             │
    ├── app/search/ ──→ cache, interface, providers│
    ├── app/file_engine/ ──→ storage, processors   │
    ├── app/voice/ ──→ providers, errors           │
    ├── app/sync/ ──→ manager, resolver, queue     │
    ├── app/plugins/ ──→ manager, tools/           │
    ├── app/automation/ ──→ models, repositories   │
    │                                             │
    ├── app/repositories/ ──→ models, core/database │
    ├── app/models/ ──→ core/database              │
    └── app/core/ ──→ config, database, logging    │
```

## Engine Dependency Graph

```
AgentService
    │
    ├── AIService ──→ AIProviderRouter
    │       └──→ OpenAIProvider, GroqProvider, GrokProvider, GeminiProvider
    │
    ├── MemoryService ──→ MemoryEngine
    │       └──→ EmbeddingService, KnowledgeGraph, EntityExtractor
    │
    ├── SearchService ──→ TavilyProvider
    │       └──→ SearchCache
    │
    ├── FileService ──→ LocalStorage
    │       └──→ TextProcessor, ImageProcessor, PDFProcessor, AudioProcessor, OCRProcessor
    │
    ├── PluginManager ──→ ToolRouter + PluginLoader
    │       └──→ 10 plugins (20 tools)
    │
    ├── VoiceService ──→ SpeechToTextProvider, TextToSpeechProvider
    │       └──→ GroqSTT/TTS, GeminiSTT/TTS, MockSTT/TTS
    │
    └── SyncService ──→ SyncManager
            └──→ ConflictResolver, SyncQueue, MockSyncProvider
```

## Service Dependency Graph

```
ChatService
    ├── AIService
    ├── MemoryService
    ├── ToolExecutor ──→ PluginManager
    ├── PromptBuilder
    └── ContextBuilder
```

## macOS Dependency Graph

```
ULTRONApp (@main)
    │
    └── AppDelegate (@MainActor)
            │
            ├── StartupSequence
            │       └── [LifecycleHook] ── sorted by StartupPhase
            │
            ├── ShutdownSequence
            │       └── [LifecycleHook] ── reverse StartupPhase
            │
            └── DependencyContainer (@MainActor)
                    ├── register(Type, factory) ──→ ServiceRegistration → ServiceRecord
                    ├── _resolve(Type) ──→ _resolveCore(oid) ──→ cache, factory, cycle
                    └── ContainerDiagnostics
                            ├── validate() ──→ _validateRecord() ──→ _resolveCore()
                            ├── registeredTypes() ──→ RegistrationSnapshot
                            ├── dependencyGraph() ──→ DependencyObserver
                            └── totalRegistrations() ──→ RegistrationStatistics

Logger (actor)
    ├── LoggerConfiguration
    │       └── minimumLevel, subsystem, destinations
    ├── LogEntry (struct, Codable, Sendable)
    │       └── timestamp, level, message, subsystem, metadata, source
    └── LogDestination (protocol)
            ├── ConsoleDestination (os_log)
            ├── FileDestination (append to file)
            └── CompositeDestination (forwards to children)
```

## Android Dependency Graph

```
UltronApp (@HiltAndroidApp)
    │
    └── MainActivity
            ├── ChatScreen ──→ ChatViewModel ──→ ChatRepository ──→ ApiService
            │                                           └──→ AppDatabase
            ├── MemoryScreen ──→ MemoryViewModel ──→ MemoryRepository ──→ ApiService
            │                                               └──→ SettingsDataStore
            ├── VoiceScreen ──→ ChatRepository
            ├── SettingsScreen ──→ SettingsViewModel ──→ SettingsDataStore
            ├── DashboardScreen
            └── OnboardingScreen ──→ SettingsDataStore
```

## Cross-Platform Pattern

```
Backend (Python)              macOS (Swift)              Android (Kotlin)
─────────────────            ──────────────             ─────────────────
Service (singleton)    →     @MainActor class     →     Hilt @Singleton
Provider (protocol)    →     Protocol              →     Interface
Repository (async)    →     actor                 →     suspend fun
Pydantic models        →     Codable struct        →     Room @Entity
PluginManager          →     DependencyContainer   →     Hilt @Module
structlog              →     Logger (actor)        →     Timber/Logcat
```

## Circular Dependencies — AUDIT

**Backend**: No circular imports detected. All imports flow downward: main → api → services → engines → repositories → models → core.

**macOS**: No circular imports. All dependencies flow Core → DI, Core → Lifecycle, Core → Logging. `ContainerResolver` has `unowned let container` to break potential retain cycle.

**Android**: Clean layered architecture. `data → domain → ui` unidirectional.

**Cross-module**: The `chat_service.py` imports from `ai/`, `memory/`, and `agent/`. These are imports from distinct engine modules, not circular dependencies. Each engine is independently testable.
