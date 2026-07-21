from __future__ import annotations

import time
from typing import Any

from app.core.logging import get_logger
from app.sync.interface import SyncAction, SyncChange, ConflictInfo

logger = get_logger(__name__)


class ResolutionStrategy:
    LAST_WRITE_WINS = "last_write_wins"
    MANUAL = "manual"
    PROVIDER_PRIORITY = "provider_priority"
    TIMESTAMP = "timestamp"


class ConflictResolver:
    def __init__(self, strategy: str = ResolutionStrategy.LAST_WRITE_WINS) -> None:
        self._strategy = strategy
        self._conflicts: list[ConflictInfo] = []

    @property
    def strategy(self) -> str:
        return self._strategy

    @strategy.setter
    def strategy(self, value: str) -> None:
        self._strategy = value

    def resolve(
        self, local: SyncChange, remote: SyncChange
    ) -> tuple[SyncChange, ConflictInfo]:
        resolution = self._strategy
        resolved: SyncChange

        if self._strategy == ResolutionStrategy.LAST_WRITE_WINS:
            lv = local.get("version", 0)
            rv = remote.get("version", 0)
            resolved = local if lv >= rv else remote
        elif self._strategy == ResolutionStrategy.TIMESTAMP:
            lt = local.get("timestamp", "")
            rt = remote.get("timestamp", "")
            resolved = local if lt >= rt else remote
        elif self._strategy == ResolutionStrategy.PROVIDER_PRIORITY:
            resolved = remote
        elif self._strategy == ResolutionStrategy.MANUAL:
            resolved = local
            resolution = "manual_local"
        else:
            resolved = local

        conflict: ConflictInfo = {
            "entity_type": local.get("entity_type", ""),
            "entity_id": local.get("entity_id", ""),
            "local_version": local.get("version", 0),
            "remote_version": remote.get("version", 0),
            "local_data": local.get("data", {}),
            "remote_data": remote.get("data", {}),
            "resolution": resolution,
        }
        self._conflicts.append(conflict)

        logger.debug(
            "conflict_resolved",
            entity_type=conflict["entity_type"],
            resolution=resolution,
        )
        return resolved, conflict

    def has_conflicts(self) -> bool:
        return len(self._conflicts) > 0

    def get_conflicts(self) -> list[ConflictInfo]:
        return list(self._conflicts)

    def clear(self) -> None:
        self._conflicts.clear()
