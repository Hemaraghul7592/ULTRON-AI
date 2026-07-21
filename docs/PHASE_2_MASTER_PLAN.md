# Phase 2 Master Plan — ULTRON AI Ecosystem

## Vision

Transform ULTRON from a single-platform AI chat app into a production-grade cross-platform AI ecosystem where the backend is the single source of truth and all clients are thin UI shells.

## Principles

1. **Backend-first architecture** — All business logic, AI orchestration, memory management, and data processing lives in the backend. Clients render UI and handle user interaction only.
2. **API-contract driven** — A single OpenAPI 3.1 specification generates client libraries for every platform. No manual DTO duplication.
3. **Offline-first with sync** — Every client maintains a local cache and syncs via the backend when connectivity is available. Conflicts are resolved server-side.
4. **Plugin system** — Third-party integrations are installable at runtime without modifying core code. Plugins are defined server-side and surfaced to all clients automatically.
5. **Vector-native memory** — All memory operations use embeddings for semantic search. The architecture supports future migration to a dedicated vector database (pgvector, Qdrant).
6. **Streaming by default** — Every AI interaction streams tokens via Server-Sent Events or WebSocket. No polling.

## Milestones

| # | Milestone | Description | Platforms |
|---|-----------|-------------|-----------|
| M1 | **AI Engine** | Unify provider interface, add model switching, smart routing, streaming, shared prompt management | Backend + Android |
| M2 | **Memory Engine** | Complete memory lifecycle, vector search, ranking, expiration, cross-session memory | Backend + Android |
| M3 | **Plugin Engine** | Dynamic plugin loading, marketplace API, permission system | Backend + Android |
| M4 | **Search Engine** | Tavily pipeline, research mode, caching, citation management | Backend + Android |
| M5 | **File Engine** | Multi-format upload, parsing, OCR, vision support | Backend + Android |
| M6 | **Voice Engine** | Real-time STT/TTS, voice conversations, wake word | Backend + Android |
| M7 | **Sync Engine** | Offline-first data sync, conflict resolution, cross-device state | All |
| M8 | **iOS Client** | Swift/SwiftUI native client | iPhone |
| M9 | **macOS Client** | Native macOS app (SwiftUI or Catalyst) | macOS |
| M10 | **Windows Client** | Native Windows app (.NET MAUI or WinUI) | Windows |
| M11 | **Desktop Suite** | Unified desktop experience across macOS + Windows | macOS, Windows |

## Dependency Graph

```
M1 (AI Engine)
├── M2 (Memory Engine) — depends on AI for embeddings
├── M3 (Plugin Engine) — depends on AI for tool execution
├── M4 (Search Engine) — depends on AI for query processing
├── M5 (File Engine)  — depends on AI for parsing
└── M6 (Voice Engine) — depends on AI for STT/TTS

M7 (Sync Engine) — depends on M1–M6 for data formats

M8 (iOS)  ─┐
M9 (macOS) ─┤── depends on M7 (Sync Engine)
M10 (Win)  ─┘
```

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Backend becomes bottleneck | High | Horizontal scaling via Docker Compose → Kubernetes |
| Sync conflicts on offline edits | Medium | CRDT-inspired last-write-wins with server-side merge |
| Plugin security | High | Sandboxed execution, permission scopes, rate limits |
| Vector search performance | Medium | Embedding caching, pgvector index tuning, future Qdrant migration |
| Cross-platform UI consistency | Low | Shared design system (Figma) + platform-native components |

## Deliverables per Milestone

Each milestone produces:
- Updated OpenAPI specification (contract-first)
- Backend implementation (services + repositories + routes)
- Android implementation (ViewModel + UI + local cache)
- Tests (backend integration + Android unit)
- Migration scripts (Alembic if schema changes)
