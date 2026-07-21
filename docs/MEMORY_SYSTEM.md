# Memory Engine — ULTRON AI Platform

## Architecture

```
            ┌─────────────────────────┐
            │   ChatService / AI      │
            │   (uses MemoryService)  │
            └───────────┬─────────────┘
                        │
                        ▼
            ┌─────────────────────────┐
            │     MemoryService       │ ← SINGLE entry point for ALL modules
            │                         │
            │  - create_memory()       │
            │  - get_memory()          │
            │  - update_memory()       │
            │  - delete_memory()       │
            │  - list_memories()       │
            │  - search_memories()     │
            │  - archive/restore()     │
            │  - get_context_for_query()│
            │  - get_stats()           │
            └───────────┬─────────────┘
                        │
                        ▼
            ┌─────────────────────────┐
            │   MemoryRepository      │
            │  (data access layer)    │
            └───────────┬─────────────┘
                        │
                        ▼
            ┌─────────────────────────┐
            │      Database           │
            │  (memories + tags)      │
            └─────────────────────────┘
```

**Design principle:** No module other than `MemoryService` accesses the memory database directly. The AI Engine, Chat, and all future modules communicate through `MemoryService` only.

## Database Schema

### `memories` table

| Column | Type | Default | Description |
|--------|------|---------|-------------|
| `id` | String(36) PK | uuid4 | Unique identifier |
| `user_id` | String(36) | — | Owner (indexed) |
| `content` | Text | — | Memory content (JSON or plain text) |
| `summary` | Text | None | Optional summary |
| `memory_type` | String(20) | `short_term` | `short_term`, `long_term`, `episodic`, `semantic` |
| `category` | String(50) | `general` | **New:** `general`, `user_profile`, `preference`, `project`, `conversation` (indexed) |
| `is_archived` | Boolean | `false` | **New:** Soft-delete flag |
| `importance` | Float | 0.5 | 0.0–1.0 importance score (indexed) |
| `access_count` | Integer | 0 | Number of retrievals |
| `embedding_vector` | Text | None | JSON-serialized embedding (future) |
| `source` | String(255) | None | Origin (chat, api, system) |
| `context` | Text | None | Extra context |
| `created_at` | DateTime | utcnow | (indexed) |
| `updated_at` | DateTime | utcnow | Auto-updated |
| `last_accessed` | DateTime | utcnow | LRU tracking |

### `tags` table

| Column | Type | Description |
|--------|------|-------------|
| `id` | String(36) PK | Unique identifier |
| `name` | String(100) | Unique tag name |
| `created_at` | DateTime | |

### `memory_tags` (associative)

| Column | Type |
|--------|------|
| `memory_id` | FK → memories.id ON DELETE CASCADE |
| `tag_id` | FK → tags.id ON DELETE CASCADE |

## Memory Categories

| Category | Purpose | Example content |
|----------|---------|-----------------|
| `general` | Default, uncategorized | Any general fact |
| `user_profile` | User identity & settings | `{"name":"Alice","timezone":"UTC","language":"en"}` |
| `preference` | User preferences | `"Dark mode"`, `"Concise responses"` |
| `project` | Project tracking | `"Build AI Engine — status: in progress"` |
| `conversation` | Conversation summaries | `"Discussed Q3 roadmap, decided on Python"` |

## Memory Lifecycle

```
Create → Active (is_archived=false)
              │
         ┌────┴────┐
         ▼         ▼
     Archived    Deleted
  (is_archived   (hard delete)
   = true)
```

## API Endpoints

### CRUD (authenticated)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/memory` | List memories (paginated, filterable) |
| POST | `/api/v1/memory` | Create a memory |
| GET | `/api/v1/memory/{id}` | Get memory by ID |
| PATCH | `/api/v1/memory/{id}` | Update memory |
| DELETE | `/api/v1/memory/{id}` | Delete memory |
| POST | `/api/v1/memory/search` | Search by content (ILIKE filter) |

### Category-specific

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/memory/profile` | Get user profile memory |
| GET | `/api/v1/memory/preferences` | List preference memories |
| GET | `/api/v1/memory/projects` | List project memories |

### Maintenance

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/memory/stats` | Memory statistics |
| PATCH | `/api/v1/memory/{id}/archive` | Archive (soft-delete) |
| PATCH | `/api/v1/memory/{id}/restore` | Restore from archive |
| PATCH | `/api/v1/memory/{id}/promote` | Promote to long-term |

### Query Parameters (for list)

- `page` (int, default 1)
- `page_size` (int, default 20, max 100)
- `memory_type` (str, optional)
- `category` (str, optional)
- `min_importance` (float, default 0.0)
- `include_archived` (bool, default false)

## AI Integration Flow

```
User Request
    │
    ▼
ChatService
    │
    ├── MemoryService.get_context_for_query() → relevant memories
    ├── AIService.chat() → AI response
    └── MemoryService.record_conversation_memory() → save summary
```

The AI Engine (`AIService` / `ChatService`) does **not** query memory storage directly. It calls `MemoryService` methods exclusively.

## Configuration

```python
# app/core/config.py
MEMORY_SHORT_TERM_MAX: int = 50       # Max short-term before summarization
MEMORY_LONG_TERM_THRESHOLD: float = 0.7  # Importance to auto-promote
MEMORY_SUMMARIZATION_THRESHOLD: int = 10  # Count trigger for compression
```

## Error Handling

| HTTP Status | Case |
|-------------|------|
| 200/201 | Success |
| 204 | Delete success (no body) |
| 401 | Missing/invalid auth token |
| 404 | Memory not found |
| 422 | Validation error |

## Class Diagram

```
MemoryService
├── create_memory(MemoryCreate, user_id) → MemoryResponse
├── get_memory(id, user_id) → MemoryResponse | None
├── update_memory(id, MemoryUpdate, user_id) → MemoryResponse | None
├── delete_memory(id, user_id) → bool
├── list_memories(user_id, **filters) → MemoryListResponse
├── search_memories(query, user_id, **filters) → list[dict]
├── archive_memory(id, user_id) → MemoryResponse | None
├── restore_memory(id, user_id) → MemoryResponse | None
├── get_profile_memory(user_id) → MemoryResponse | None
├── get_preferences(user_id) → list[MemoryResponse]
├── get_project_memories(user_id) → list[MemoryResponse]
├── get_context_for_query(query, user_id, limit, categories) → str
├── record_conversation_memory(summary, user_id, importance) → MemoryResponse
└── get_stats(user_id) → dict

MemoryRepository
├── create(MemoryCreate, user_id, embedding) → Memory
├── get(id, user_id) → Memory | None
├── list_all(user_id, page, page_size, memory_type, category, min_importance, include_archived) → (list[Memory], int)
├── update(id, dict, user_id) → Memory | None
├── delete(id, user_id) → bool
├── search_by_content(query, user_id, limit, memory_type, category, min_importance) → list[Memory]
├── get_by_category(category, user_id, limit) → list[Memory]
├── get_by_type(memory_type, user_id, limit) → list[Memory]
├── increment_access(id, user_id) → None
└── promote_to_long_term(user_id, threshold) → int
```

## Future Roadmap

| Milestone | Feature | Status |
|-----------|---------|--------|
| M2 | Structured categories (profile, preference, project) | ✅ Done |
| M2 | Archive/restore | ✅ Done |
| M2 | Category-specific API endpoints | ✅ Done |
| Future | Vector embeddings & semantic search | ⏳ Planned |
| Future | Automatic memory consolidation | ⏳ Planned |
| Future | Memory ranking & reflection | ⏳ Planned |
| Future | Knowledge graph integration | ⏳ Planned |
| Future | Cross-user memory sharing | ⏳ Planned |
