# Sync Engine — ULTRON AI

## Architecture

```
SyncService (single entry point)
        │
        ├── SyncManager
        │       │
        │       ├── SyncProvider interface
        │       │       └── MockSyncProvider (testing)
        │       │
        │       ├── ConflictResolver (4 strategies)
        │       │
        │       └── SyncQueue (in-memory, retry, backoff)
        │
        └── Change Tracking (created/updated/deleted/moved)
```

## Core Files

| File | Purpose |
|------|---------|
| `app/sync/interface.py` | `SyncProvider` ABC + types (`SyncChange`, `SyncResult`, `SyncState`, `SyncAction`, `SyncStatus`) |
| `app/sync/errors.py` | `SyncError` hierarchy (6 types) |
| `app/sync/models.py` | Model helpers (`make_change`, `change_key`, `is_older`, `merge_changes`, `compute_checksum`) |
| `app/sync/resolver.py` | `ConflictResolver` with 4 built-in strategies |
| `app/sync/queue.py` | `SyncQueue` — in-memory with exponential backoff retry |
| `app/sync/manager.py` | `SyncManager` — coordinates providers, queue, conflict resolver |
| `app/sync/service.py` | `SyncService` — single public API entry point |
| `app/sync/providers/mock.py` | `MockSyncProvider` for testing |

## SyncProvider Interface

| Method | Returns | Description |
|--------|---------|-------------|
| `push(changes)` | `SyncResult` | Send local changes to provider |
| `pull(since)` | `list[SyncChange]` | Get remote changes since timestamp |
| `list_changes(since)` | `list[SyncChange]` | List available remote changes |
| `health_check()` | `dict` | Provider health |
| `validate()` | `bool` | Credentials/configuration check |
| `metadata()` | `dict` | Provider name, version, supported actions |

## SyncAction Enum

| Value | Description |
|-------|-------------|
| `create` | New entity created |
| `update` | Entity modified |
| `delete` | Entity removed |
| `move` | Entity relocated |

## SyncService API

| Method | Description |
|--------|-------------|
| `register_provider(provider)` | Register a sync provider |
| `unregister_provider(name)` | Remove a provider |
| `list_providers()` | List registered provider names |
| `get_provider(name)` | Get provider by name |
| `push(provider, changes)` | Push local changes to provider |
| `pull(provider, since)` | Pull remote changes |
| `sync(provider)` | Full sync: pull → resolve conflicts → push |
| `track_change(provider, change)` | Record local change for later sync |
| `get_tracked_changes(provider)` | Get all pending local changes |
| `get_sync_state(provider)` | Get provider sync state |
| `health_check(provider?)` | Health check specific or all providers |

## ConflictResolver Strategies

| Strategy | Logic |
|----------|-------|
| `last_write_wins` | Higher version number wins |
| `timestamp` | Newer timestamp wins |
| `provider_priority` | Remote (provider) always wins |
| `manual` | Local wins, marked for user resolution |

## SyncQueue

- In-memory operation queue with UUIDs
- Exponential backoff: `delay = base_delay × 2^(attempt-1)` (capped at max_delay)
- Configurable retry count per item
- `process_all()` — drain queue
- `process_one(id)` — process single item
- `cancel(id)` / `cancel_all()` — abort operations
- Status tracking: pending, in_progress, completed, failed

## Change Tracking

`SyncChange` tracks:
- `entity_type` — e.g. "memories", "conversations", "files"
- `entity_id` — UUID string
- `action` — create/update/delete/move
- `data` — entity payload as dict
- `version` — monotonically increasing
- `checksum` — SHA-256 of data for integrity
- `timestamp` — ISO 8601
- `source` — "local" or provider name

## Error Hierarchy

```
SyncError
├── ProviderUnavailableError
├── ConflictError (carries conflict details)
├── RetryExceededError
├── AuthenticationError
├── QueueError
```

## Integration Points

- **FileService**: Sync files through `SyncProvider` push/pull (no direct filesystem access)
- **MemoryService**: Track memory changes via `track_change()`
- **PluginManager**: Google Drive provider implementation uses existing Google OAuth

## Future Extensibility

- Persist queue to DB for crash recovery
- Add WebSocket push notifications for real-time sync
- Implement `GoogleDriveSyncProvider` wrapping existing Google Drive plugin
- Add `DropboxSyncProvider`, `OneDriveSyncProvider`, `iCloudSyncProvider`
- Client-server sync API endpoints at `/api/v1/sync/`

## Tests

`tests/test_sync.py` — 60 tests covering:
- Models (checksum, make_change, change_key, is_older, merge_changes)
- ConflictResolver (all 4 strategies, clear, switch, conflict info)
- SyncQueue (enqueue, process, retry, max retries, cancel, stats, clear)
- SyncManager (register, unregister, list, push, pull, sync, track, state, health)
- SyncService (register, push, pull, sync, health, list, unregister, track, state)
- Error hierarchy + conflict error payload
- MockSyncProvider (push, pull, fail, pushed tracking, health, validate, metadata)
