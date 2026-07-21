from __future__ import annotations

import abc
import enum
from typing import Any, TypedDict


class SyncAction(str, enum.Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    MOVE = "move"


class SyncStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CONFLICT = "conflict"


class SyncChange(TypedDict, total=False):
    entity_type: str
    entity_id: str
    action: SyncAction
    data: dict[str, Any]
    version: int
    checksum: str
    timestamp: str
    source: str


class SyncResult(TypedDict, total=False):
    status: SyncStatus
    changes_processed: int
    conflicts: list[dict[str, Any]]
    errors: list[str]
    provider: str
    synced_at: str


class SyncState(TypedDict, total=False):
    last_sync_at: str
    last_sync_version: int
    pending_count: int
    provider: str


class ConflictInfo(TypedDict, total=False):
    entity_type: str
    entity_id: str
    local_version: int
    remote_version: int
    local_data: dict[str, Any]
    remote_data: dict[str, Any]
    resolution: str


class SyncProvider(abc.ABC):
    @property
    @abc.abstractmethod
    def name(self) -> str:
        pass

    @abc.abstractmethod
    async def push(self, changes: list[SyncChange]) -> SyncResult:
        pass

    @abc.abstractmethod
    async def pull(self, since: str | None = None) -> list[SyncChange]:
        pass

    @abc.abstractmethod
    async def list_changes(self, since: str | None = None) -> list[SyncChange]:
        pass

    async def health_check(self) -> dict[str, Any]:
        return {"status": "available", "provider": self.name}

    async def validate(self) -> bool:
        return True

    def metadata(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": "1.0.0",
            "supported_actions": [a.value for a in SyncAction],
        }
