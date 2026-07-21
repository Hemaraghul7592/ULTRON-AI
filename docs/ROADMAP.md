# Phase 2 Roadmap — ULTRON AI Ecosystem

## Timeline Overview

```
M1: AI Engine       ████████░░░░░░░░░░░░  8 weeks (weeks 1–8)
M2: Memory Engine   ░░░░████████░░░░░░░░  8 weeks (weeks 5–12)
M3: Plugin Engine   ░░░░░░░░████████░░░░  8 weeks (weeks 9–16)
M4: Search Engine   ░░░░░░░░░░██████░░░░  6 weeks (weeks 11–16)
M5: File Engine     ░░░░░░░░░░░░████████  8 weeks (weeks 13–20)
M6: Voice Engine    ░░░░░░░░░░░░░░██████  6 weeks (weeks 15–20)
M7: Sync Engine     ░░░░░░░░░░░░░░░░████  4 weeks (weeks 17–20)
M8: iOS Client      ░░░░░░░░░░░░░░░░░░██  8 weeks (weeks 21–28)
M9: macOS Client    ░░░░░░░░░░░░░░░░░░░░  6 weeks (weeks 25–30)
M10: Windows Client ░░░░░░░░░░░░░░░░░░░░  8 weeks (weeks 25–32)
M11: Desktop Suite  ░░░░░░░░░░░░░░░░░░░░  4 weeks (weeks 31–34)
```

## Milestone Details

### M1: AI Engine (Weeks 1–8)

**Goal**: Unify all AI providers behind a single interface with streaming, routing, and prompt management.

**Deliverables**:
- [x] `AIProvider` abstract base class (existing — refine)
- [ ] Unified streaming protocol (SSE)
- [ ] Provider Router with strategies (manual, cost, capability, fallback)
- [ ] Model registry (configurable via settings)
- [ ] Token budget management
- [ ] Prompt builder with memory injection
- [ ] OpenAPI client SDK for chat endpoints
- [ ] Android: migrate ChatViewModel to use generated SDK
- [ ] Tests: every provider, every routing strategy, streaming

**Backend files**: `app/ai/`, `app/schemas/ai.py`, `app/api/v1/chat.py`
**Android files**: `data/remote/ApiService.kt` → SDK, `ui/screens/chat/`

### M2: Memory Engine (Weeks 5–12)

**Goal**: Complete memory lifecycle with vector search, ranking, consolidation, and expiration.

**Deliverables**:
- [ ] Memory classification pipeline
- [ ] Embedding service (sentence-transformers → pgvector)
- [ ] Memory retrieval with RRF fusion
- [ ] Memory consolidation scheduler
- [ ] Importance scoring
- [ ] TTL expiration for short-term memories
- [ ] Android: MemoryViewModel → sync-aware, vector search UI
- [ ] Database migration (memory schema enhancements)

**Backend files**: `app/memory/`, `app/schemas/memory.py`, new repository methods
**Database**: Migration V2 (add memory columns)

### M3: Plugin Engine (Weeks 9–16)

**Goal**: Dynamic plugin system with marketplace, permissions, and configuration UI.

**Deliverables**:
- [ ] Plugin manifest loader
- [ ] Plugin sandbox (timeout, memory, network restrictions)
- [ ] Marketplace API
- [ ] Per-user plugin config
- [ ] OAuth integration for plugins
- [ ] Dynamic UI schema (JSON forms)
- [ ] Android: Plugin management screen
- [ ] Tests: plugin isolation, marketplace flow

### M4: Search Engine (Weeks 11–16)

**Goal**: Production search pipeline with Tavily, caching, deep research, and citation management.

**Deliverables**:
- [ ] Search pipeline (query → cache → Tavily → process)
- [ ] Deep research mode (multi-query + aggregation)
- [ ] Search caching (Redis)
- [ ] Search history API + UI
- [ ] Citation formatting for LLM context
- [ ] Android: search UI integration

### M5: File Engine (Weeks 13–20)

**Goal**: Multi-format file upload, parsing, storage, and AI context injection.

**Deliverables**:
- [ ] File upload API (multipart)
- [ ] PDF/DOCX/TXT/CSV/JSON parsers
- [ ] S3-compatible storage adapter
- [ ] File → AI context pipeline
- [ ] OCR for images (Tesseract)
- [ ] Android: file picker + upload UI

### M6: Voice Engine (Weeks 15–20)

**Goal**: Real-time voice conversations with streaming STT/TTS and session management.

**Deliverables**:
- [ ] WebSocket voice session
- [ ] STT provider integration (Groq Whisper, Gemini)
- [ ] TTS provider integration (Groq PlayAI, Gemini)
- [ ] Voice pipeline (STT → AI → TTS)
- [ ] Android: real-time voice UI
- [ ] Latency optimization

### M7: Sync Engine (Weeks 17–20)

**Goal**: Offline-first sync across all platforms.

**Deliverables**:
- [ ] Sync API (push, pull, status, resolve)
- [ ] Sync log table
- [ ] Conflict resolution (LWW)
- [ ] Android: SyncManager + OutboxQueue
- [ ] iOS: SyncManager stub
- [ ] Desktop: SyncManager stub
- [ ] Backend sync orchestration

### M8: iOS Client (Weeks 21–28)

**Goal**: Native iOS app with full feature parity.

**Deliverables**:
- [ ] Project scaffold (SwiftUI + Swift Package Manager)
- [ ] Generated OpenAPI SDK
- [ ] Auth flow (login, register, token storage)
- [ ] Chat screen (streaming)
- [ ] Memory screen
- [ ] Settings screen
- [ ] iOS-specific UI (navigation patterns, gestures)

### M9: macOS Client (Weeks 25–30)

**Goal**: Native macOS app (SwiftUI Mac Catalyst or AppKit).

**Deliverables**:
- [ ] macOS project scaffold
- [ ] Shared code with iOS (Swift Package)
- [ ] Desktop-specific UI (menu bar, keyboard shortcuts, window management)

### M10: Windows Client (Weeks 25–32)

**Goal**: Native Windows app.

**Deliverables**:
- [ ] Project scaffold (.NET MAUI or Tauri)
- [ ] Generated OpenAPI SDK (TypeScript or C#)
- [ ] Desktop UI (WinUI or web-based)
- [ ] Windows-specific features (system tray, notifications)

### M11: Desktop Suite (Weeks 31–34)

**Goal**: Unified desktop experience across macOS + Windows.

**Deliverables**:
- [ ] Design system parity
- [ ] Cross-platform testing
- [ ] Keyboard shortcut consistency
- [ ] Accessibility review
- [ ] Performance profiling

## Dependency & Risk Tracking

| Milestone | Blocked By | Risk Level | Mitigation |
|-----------|-----------|------------|------------|
| M1 AI Engine | — | Low | Providers already exist, need unification |
| M2 Memory | M1 (embeddings) | Medium | Embedding model selection, pgvector setup |
| M3 Plugins | — | Medium | Security sandbox design |
| M4 Search | — | Low | Tavily API already integrated |
| M5 Files | — | Medium | PDF parsing quality varies |
| M6 Voice | M1 (streaming) | Medium | Real-time audio latency |
| M7 Sync | M1–M6 | High | Conflict resolution complex |
| M8 iOS | M7 (sync) | Medium | New platform, new language |
| M9 macOS | M8 (shared code) | Low | Shared Swift code |
| M10 Windows | — | Medium | New ecosystem (.NET or Tauri) |
| M11 Desktop | M9, M10 | Low | Polish pass |

## Success Criteria

By the end of Phase 2:

1. Three production clients (Android, iOS, Desktop) with feature parity
2. All AI interactions stream via unified protocol
3. Memory system is vector-native with semantic search
4. Plugin system supports dynamic installation
5. File engine handles all common formats
6. Voice engine enables real-time conversations
7. Sync engine keeps all devices consistent
8. Single OpenAPI spec drives all client SDKs
9. Zero manual DTO duplication between backend and clients
10. CI/CD for all platforms
