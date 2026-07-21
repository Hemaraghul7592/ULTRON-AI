# System Architecture — ULTRON AI Ecosystem

## Overview

```
┌─────────────────────────────────────────────────────────┐
│                    BACKEND (FastAPI)                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │ AI       │ │ Memory   │ │ Plugin   │ │ Voice    │   │
│  │ Engine   │ │ Engine   │ │ Engine   │ │ Engine   │   │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘   │
│  ┌────┴─────┐ ┌────┴─────┐ ┌────┴─────┐ ┌────┴─────┐   │
│  │ Search   │ │ File     │ │ Sync     │ │ Auth     │   │
│  │ Engine   │ │ Engine   │ │ Engine   │ │ Service  │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │           REST API + WebSocket                   │   │
│  └──────────────────────┬───────────────────────────┘   │
└─────────────────────────┼───────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
     ┌────┴────┐    ┌────┴────┐    ┌─────┴─────┐
     │ Android │    │  iOS    │    │  Desktop  │
     │ (Kotlin │    │ (Swift  │    │ (Tauri /  │
     │ Compose)│    │ SwiftUI)│    │  Native)  │
     └─────────┘    └─────────┘    └───────────┘
```

## Layer Architecture

### Backend Layers

```
┌──────────────────────────────────────────────────┐
│                  API Layer (Routers)              │
│  auth  chat  memory  search  files  plugins      │
│  voice  conversations  entities  tools  sync      │
│  observability  admin                             │
├──────────────────────────────────────────────────┤
│               Service Layer                       │
│  AuthService  ChatService  SyncService            │
│  GoogleOAuth  VoicePipeline                       │
├──────────────────────────────────────────────────┤
│             Engine Layer                          │
│  AI Engine  Memory Engine  Plugin Engine          │
│  Search Engine  File Engine  Voice Engine         │
├──────────────────────────────────────────────────┤
│            Repository Layer (Data Access)         │
│  UserRepo  ConversationRepo  MemoryRepo           │
│  TaskRepo  EntityRepo  MetricRepo  SyncRepo       │
├──────────────────────────────────────────────────┤
│            Infrastructure Layer                   │
│  Database (SQLAlchemy)  Redis  Object Storage     │
│  Message Queue  Vector Store  Cache               │
└──────────────────────────────────────────────────┘
```

### Client Layers (each platform)

```
┌──────────────────────────────────────────────────┐
│                  UI Layer                          │
│  Screens  Components  Navigation  Themes          │
├──────────────────────────────────────────────────┤
│              ViewModel / State Layer              │
│  Screen state  UI events  Local state             │
├──────────────────────────────────────────────────┤
│              Sync Layer (shared logic)            │
│  Offline queue  Conflict resolver  Sync manager   │
├──────────────────────────────────────────────────┤
│              Data Layer                           │
│  Local DB (Room / CoreData / SQLite)              │
│  HTTP client (generated from OpenAPI)             │
│  WebSocket client  Cache                          │
└──────────────────────────────────────────────────┘
```

## Communication Patterns

### REST API (request-response)
- CRUD operations, auth, file uploads
- JSON payloads, multipart for files
- Bearer token auth

### Server-Sent Events (streaming)
- AI chat streaming (`/chat/stream`)
- Real-time notifications
- Lightweight, unidirectional

### WebSocket (bidirectional)
- Voice session management
- Sync events (push-based)
- Real-time collaboration (future)

## Current Architecture Weaknesses

| Issue | Impact | Phase 2 Solution |
|-------|--------|------------------|
| No shared API contract | DTOs duplicated across backend Pydantic and Android data classes | OpenAPI 3.1 spec → code generation for all clients |
| Android Room entities don't match backend | Data loss on sync, manual mapping | Unified schema + auto-generated client entities |
| No offline queue | Requests silently fail without network | Offline-first with retry queue and conflict resolution |
| Auth token stored in DataStore without refresh | Token expiry breaks app | Refresh token flow + secure storage |
| No WebSocket | No push-based sync or real-time features | WebSocket for sync events, notifications |
| Voice screen is placeholder | No voice functionality | Voice engine with WebSocket-based sessions |
| Dashboard screen is placeholder | No real metrics visualization | Live dashboard with streaming metrics |
| No iOS client | iPhone users excluded | Swift/SwiftUI native client |
| No desktop clients | macOS/Windows users excluded | Tauri (Rust) or native clients |
| Plugin UI not surfaced | Backend plugins invisible to user | Plugin discovery UI + dynamic form rendering |
| Single-server architecture | No horizontal scaling | Stateless design with Redis session store |
| No CI/CD for Android | No automated build verification | GitHub Actions for Android build + test |

## Recommended Project Structure Changes

### Current → Recommended

```
ULTRON-AI/
├── backend/          ← stays as-is (expand within)
├── android/          ← stays as-is (expand within)
├── docs/             ← NEW: Phase 2 documentation
├── api/              ← NEW: OpenAPI 3.1 specification
│   ├── openapi.yaml
│   └── components/
├── clients/          ← NEW: Generated client libraries
│   ├── kotlin/       ← Android SDK
│   ├── swift/        ← iOS SDK
│   └── typescript/   ← Desktop SDK
├── ios/              ← NEW: iOS app (Swift/SwiftUI)
├── desktop/          ← NEW: Desktop app (Tauri)
└── scripts/          ← NEW: DevOps, codegen, migration scripts
```

### Why Not Move Files Yet

Phase 1 is stable. The structural changes above are recommendations for Phase 2 implementation. Move incrementally:

1. Create `api/` directory with OpenAPI spec
2. Generate client SDKs into `clients/`
3. Create `ios/` and `desktop/` when those milestones begin
4. Keep `android/` in place — the OpenAPI-generated SDK replaces manual DTOs

## Technology Choices for Phase 2

| Component | Technology | Rationale |
|-----------|------------|-----------|
| API specification | OpenAPI 3.1 | Industry standard, codegen support |
| Client codegen | OpenAPI Generator | Supports Kotlin, Swift, TypeScript |
| iOS UI | SwiftUI | Modern, declarative, cross-device |
| macOS UI | SwiftUI (Mac Catalyst) | Shared code with iOS |
| Windows UI | .NET MAUI or WinUI 3 | Native Windows experience |
| Desktop cross-platform | Tauri (Rust) | Lightweight, secure, any frontend |
| Vector storage | pgvector (initially), Qdrant (future) | No infra change for v1, dedicated DB later |
| Object storage | S3-compatible (MinIO / Cloudflare R2) | File storage for all platforms |
| Message queue | Redis Streams or RabbitMQ | Background job processing |
| Real-time | WebSocket (FastAPI native) | No additional infra needed |
| CI/CD | GitHub Actions | Already in use for backend |
