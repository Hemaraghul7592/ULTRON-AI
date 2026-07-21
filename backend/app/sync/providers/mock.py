from __future__ import annotations

import time

from app.sync.interface import SyncChange, SyncProvider, SyncResult


class MockSyncProvider(SyncProvider):
    def __init__(
        self,
        name: str = "mock",
        push_result: SyncResult | None = None,
        pull_changes: list[SyncChange] | None = None,
        should_fail_push: bool = False,
        should_fail_pull: bool = False,
        fail_reason: str = "mock error",
    ) -> None:
        self._name = name
        self._push_result = push_result or SyncResult(
            status="completed",
            changes_processed=0,
            conflicts=[],
            errors=[],
        )
        self._pull_changes = pull_changes or []
        self._should_fail_push = should_fail_push
        self._should_fail_pull = should_fail_pull
        self._fail_reason = fail_reason
        self._pushed: list[list[SyncChange]] = []

    @property
    def name(self) -> str:
        return self._name

    async def push(self, changes: list[SyncChange]) -> SyncResult:
        if self._should_fail_push:
            raise RuntimeError(self._fail_reason)
        self._pushed.append(changes)
        result = dict(self._push_result)
        result["changes_processed"] = len(changes)
        result["synced_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        result["provider"] = self._name
        return SyncResult(**result)

    async def pull(self, since: str | None = None) -> list[SyncChange]:
        if self._should_fail_pull:
            raise RuntimeError(self._fail_reason)
        return list(self._pull_changes)

    async def list_changes(self, since: str | None = None) -> list[SyncChange]:
        return list(self._pull_changes)

    @property
    def pushed(self) -> list[list[SyncChange]]:
        return self._pushed

    def set_pull_changes(self, changes: list[SyncChange]) -> None:
        self._pull_changes = changes
