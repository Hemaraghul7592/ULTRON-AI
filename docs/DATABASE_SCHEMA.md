# Database Schema — ULTRON AI Platform

## Design Principles

1. **Backend owns the schema** — All tables are defined in SQLAlchemy models. Clients mirror a subset for offline cache.
2. **UUID primary keys** — Enables offline ID generation without conflicts.
3. **Soft deletes** — `deleted_at` timestamp instead of hard deletes for recoverability and sync.
4. **Vector columns** — pgvector for embeddings (future Qdrant migration supported via dual-write pattern).
5. **Timestamps on every row** — `created_at` and `updated_at` for sync ordering.

## Entity Relationship Diagram

```
users ──────┬── conversations ──┬── messages
            ├── memories ───────┬── memory_tags ──┬── tags
            ├── tasks
            ├── entities ───────┬── relationships
            ├── token_usage
            ├── metrics
            ├── google_tokens
            ├── files           ← NEW
            ├── search_history   ← NEW
            ├── plugin_configs   ← NEW
            ├── sync_log         ← NEW
            └── sessions         ← NEW (refresh tokens)
```

## Tables

### users (existing — enhance)

```sql
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username        VARCHAR(50) UNIQUE NOT NULL,
    email           VARCHAR(255) UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    display_name    VARCHAR(100),          -- NEW
    avatar_url      TEXT,                   -- NEW
    is_active       BOOLEAN DEFAULT TRUE,
    is_verified     BOOLEAN DEFAULT FALSE,  -- NEW
    preferences     JSONB DEFAULT '{}',     -- NEW: all user settings
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ             -- NEW: soft delete
);
```

### sessions (NEW — refresh token management)

```sql
CREATE TABLE sessions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    refresh_token   VARCHAR(255) UNIQUE NOT NULL,
    device_info     VARCHAR(255),           -- "Android 14 / Pixel 8"
    platform        VARCHAR(20),            -- "android", "ios", "macos", "windows"
    ip_address      INET,
    expires_at      TIMESTAMPTZ NOT NULL,
    revoked_at      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_refresh_token ON sessions(refresh_token);
```

### conversations (existing — add columns)

```sql
CREATE TABLE conversations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title           VARCHAR(255),
    model           VARCHAR(100),
    system_prompt   TEXT,
    metadata        JSONB DEFAULT '{}',            -- NEW: tags, folder, color
    is_archived     BOOLEAN DEFAULT FALSE,          -- NEW
    is_pinned       BOOLEAN DEFAULT FALSE,          -- NEW
    sync_version    INTEGER DEFAULT 1,              -- NEW: optimistic concurrency
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ
);
```

### messages (existing — enhance)

```sql
CREATE TABLE messages (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role            VARCHAR(20) NOT NULL,   -- "user", "assistant", "system", "tool"
    content         TEXT NOT NULL,
    model           VARCHAR(100),
    tokens_used     INTEGER,
    tool_calls      JSONB,
    metadata        JSONB DEFAULT '{}',
    parent_id       UUID REFERENCES messages(id),   -- NEW: branching
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ
);
CREATE INDEX idx_messages_conversation ON messages(conversation_id, created_at);
```

### memories (existing — enhance)

```sql
CREATE TABLE memories (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content         TEXT NOT NULL,
    summary         TEXT,
    memory_type     VARCHAR(20) DEFAULT 'short_term',
                    -- "short_term", "long_term", "episodic", "semantic", "procedural"
    importance      FLOAT DEFAULT 0.5,
    access_count    INTEGER DEFAULT 0,
    embedding       VECTOR(384),                    -- pgvector (future)
    source          VARCHAR(50),                    -- "chat", "manual", "file", "system"
    context         JSONB DEFAULT '{}',             -- NEW: associated conversation, file IDs
    tags            TEXT[] DEFAULT '{}',             -- NEW: native array, avoid join
    expires_at      TIMESTAMPTZ,                    -- NEW: TTL for short-term
    last_accessed   TIMESTAMPTZ DEFAULT NOW(),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ
);
CREATE INDEX idx_memories_user_type ON memories(user_id, memory_type);
CREATE INDEX idx_memories_importance ON memories(user_id, importance DESC);
CREATE INDEX idx_memories_embedding ON memories USING ivfflat (embedding vector_cosine_ops);
```

### tags (existing — simplify via native arrays)

Keep for metadata, but memories use native `TEXT[]` instead of join table. Tags table for plugin-defined tags.

### files (NEW)

```sql
CREATE TABLE files (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename        VARCHAR(255) NOT NULL,
    original_name   VARCHAR(255) NOT NULL,
    mime_type       VARCHAR(100) NOT NULL,
    size_bytes      BIGINT NOT NULL,
    storage_path    TEXT NOT NULL,           -- S3 key or local path
    storage_backend VARCHAR(20) DEFAULT 'local',  -- "local", "s3", "r2"
    checksum        VARCHAR(64),            -- SHA-256
    parsed_content  TEXT,                   -- Extracted text
    parsed_at       TIMESTAMPTZ,
    metadata        JSONB DEFAULT '{}',     -- EXIF, document stats
    conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ
);
CREATE INDEX idx_files_user ON files(user_id);
```

### search_history (NEW)

```sql
CREATE TABLE search_history (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    query           TEXT NOT NULL,
    results         JSONB,                  -- Cached results
    source          VARCHAR(20) DEFAULT 'tavily',
    is_research     BOOLEAN DEFAULT FALSE,
    tokens_used     INTEGER,
    cached_until    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_search_history_user ON search_history(user_id, created_at DESC);
```

### plugin_configs (NEW)

```sql
CREATE TABLE plugin_configs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plugin_name     VARCHAR(100) NOT NULL,
    enabled         BOOLEAN DEFAULT TRUE,
    config          JSONB DEFAULT '{}',     -- Plugin-specific settings
    permissions     JSONB DEFAULT '{}',     -- Scopes granted by user
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, plugin_name)
);
```

### sync_log (NEW)

```sql
CREATE TABLE sync_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    device_id       VARCHAR(100) NOT NULL,
    entity_type     VARCHAR(50) NOT NULL,   -- "conversations", "memories", etc.
    entity_id       UUID NOT NULL,
    action          VARCHAR(20) NOT NULL,   -- "create", "update", "delete"
    version         INTEGER NOT NULL,
    checksum        VARCHAR(64),
    synced_at       TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_sync_log_user ON sync_log(user_id, synced_at DESC);
CREATE INDEX idx_sync_log_entity ON sync_log(entity_type, entity_id);
```

### tasks (existing — already robust)

No major changes needed. Minor additions:

```sql
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS parent_task_id UUID REFERENCES tasks(id);
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}';
```

## Android Room Schema (Local Cache)

```kotlin
// Mirrors backend schema with sync metadata
@Entity(tableName = "conversations")
data class ConversationEntity(
    @PrimaryKey val id: String,           // UUID from backend
    val title: String?,
    val model: String?,
    val systemPrompt: String?,
    val isPinned: Boolean = false,
    val isArchived: Boolean = false,
    val syncVersion: Int = 0,
    val isDirty: Boolean = false,          // NEW: pending sync
    val lastSyncedAt: Long? = null,
    val createdAt: Long,
    val updatedAt: Long,
    val deletedAt: Long? = null
)
```

## Migration Strategy

```
Current: Version 1 (4 Alembic migrations)
Phase 2:
  Version 2 — Add files, sessions, plugin_configs tables
  Version 3 — Add sync_log table
  Version 4 — Add columns to existing tables (preferences, metadata, etc.)
  Version 5 — Migrate memory_tags to native TEXT[] arrays
```

Each migration is backward-compatible. Clients that haven't updated continue to work with reduced functionality.
