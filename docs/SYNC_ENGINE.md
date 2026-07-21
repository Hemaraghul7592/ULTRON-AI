# Sync Engine — ULTRON AI Platform

## Architecture

```
┌──────────┐         ┌──────────┐         ┌──────────┐
│  Android  │         │   iOS    │         │  Desktop │
│  (offline)│         │ (offline)│         │ (offline)│
└─────┬────┘         └────┬─────┘         └────┬─────┘
      │                   │                    │
      ▼                   ▼                    ▼
┌─────────────────────────────────────────────────────┐
│              Sync API (Backend)                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ │
│  │Pull      │ │Push      │ │Conflict  │ │Status  │ │
│  │Changes   │ │Changes   │ │Resolve   │ │Check   │ │
│  └──────────┘ └──────────┘ └──────────┘ └────────┘ │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │           Sync Log (source of truth)          │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

## Sync Strategy: Last-Write-Wins with Version Vector

```
Each entity has:
  - sync_version (integer, incremented on each change)
  - updated_at (timestamp)
  - checksum (SHA-256 of serialized entity)

Conflict resolution:
  - Higher sync_version wins
  - If same version → higher checksum wins (deterministic)
  - Client always accepts server version on conflict
  - Server logs conflict for auditing
```

## Push Flow

```
Client:
  1. Collect all entities where isDirty = true
  2. Send batch to POST /sync/push
  3. Server:
     a. For each entity, check sync_version
     b. If client version < server version → conflict
     c. If client version >= server version → accept and increment
     d. Return updated entities with new versions

Server Response:
{
  "accepted": [{"type": "conversation", "id": "uuid", "new_version": 5}],
  "conflicts": [{"type": "memory", "id": "uuid", "server_version": 3, "client_version": 2}],
  "rejected": [] // version too old, deleted entity, etc.
}
```

## Pull Flow

```
Client:
  1. Send last_synced_at timestamp
  2. POST /sync/pull

Server:
  1. Query sync_log for changes since timestamp
  2. Return all changed entities for this user

Server Response:
{
  "changes": [
    {"type": "conversation", "action": "update", "data": {...}, "version": 5},
    {"type": "memory", "action": "delete", "id": "uuid"},
  ],
  "server_time": "2026-07-21T12:00:00Z",
  "has_more": false
}
```

## Offline Queue (Client-Side)

```
┌──────────────────────┐
│    SyncManager        │
│                       │
│  ┌─────────────────┐  │
│  │  Outbox Queue    │  │
│  │  (PendingOps DB) │  │
│  │  - create conv   │  │
│  │  - update mem    │  │
│  │  - delete msg    │  │
│  └────────┬────────┘  │
│           │           │
│           ▼           │
│  ┌─────────────────┐  │
│  │  Sync Scheduler  │  │
│  │  - On network    │  │
│  │  - Periodic      │  │
│  │  - Manual        │  │
│  └─────────────────┘  │
└──────────────────────┘
```

## Synced Entity Types

| Entity | Sync Direction | Conflict | Priority |
|--------|---------------|----------|----------|
| Conversations | Bidirectional | LWW | High |
| Messages | Client → Server (append-only) | None | High |
| Memories | Bidirectional | LWW | Medium |
| Settings | Bidirectional | LWW | Medium |
| Files | Client → Server | None | Low |
| Plugin configs | Bidirectional | LWW | Low |
| Search history | Client → Server | None | Low |

## Initial Sync

On first login after a period of being offline:

```
1. Client sends all local data as "push"
2. Server accepts and returns server-state
3. Client overwrites local with server state
4. Client resubmits any local-only data
```

## Android Implementation

```kotlin
class SyncManager @Inject constructor(
    private val api: SyncApi,
    private val db: AppDatabase,
) {
    private val outbox = OutboxQueue(db)

    suspend fun pushChanges() {
        val pending = outbox.getAll()
        if (pending.isEmpty()) return

        val response = api.push(SyncPushRequest(changes = pending))
        response.accepted.forEach { markSynced(it.id, it.newVersion) }
        response.conflicts.forEach { resolveConflict(it) }
    }

    suspend fun pullChanges() {
        val lastSync = prefs.lastSyncTime
        val response = api.pull(SyncPullRequest(since = lastSync))

        response.changes.forEach { change ->
            when (change.action) {
                "create" -> upsertLocal(change)
                "update" -> upsertLocal(change)
                "delete" -> deleteLocal(change)
            }
        }
        prefs.lastSyncTime = response.serverTime
    }
}
```

## Error Handling

| Error | Client Action |
|-------|---------------|
| Network unavailable | Queue, retry with exponential backoff |
| Server 401 | Logout, re-authenticate, retry |
| Server 409 (conflict) | Accept server version, notify user |
| Server 5xx | Retry with backoff (max 3 attempts) |
| Payload too large | Batch split |
