from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.sync.interface import SyncChange, SyncProvider, SyncResult  # noqa: TC001
from app.sync.manager import SyncManager

logger = get_logger(__name__)


class SyncService:
    def __init__(self, manager: SyncManager | None = None) -> None:
        self._manager = manager or SyncManager()

    @property
    def manager(self) -> SyncManager:
        return self._manager

    def register_provider(self, provider: SyncProvider) -> None:
        self._manager.register_provider(provider)

    def unregister_provider(self, name: str) -> bool:
        return self._manager.unregister_provider(name)

    def list_providers(self) -> list[str]:
        return self._manager.list_providers()

    def get_provider(self, name: str) -> SyncProvider | None:
        return self._manager.get_provider(name)

    async def push(self, provider_name: str, changes: list[SyncChange]) -> SyncResult:
        return await self._manager.push(provider_name, changes)

    async def pull(self, provider_name: str, since: str | None = None) -> list[SyncChange]:
        return await self._manager.pull(provider_name, since)

    async def sync(self, provider_name: str) -> SyncResult:
        return await self._manager.sync(provider_name)

    def track_change(self, provider_name: str, change: SyncChange) -> None:
        self._manager.track_change(provider_name, change)

    def get_tracked_changes(self, provider_name: str) -> list[SyncChange]:
        return self._manager.get_tracked_changes(provider_name)

    def get_sync_state(self, provider_name: str) -> dict[str, Any] | None:
        state = self._manager.get_state(provider_name)
        if state is None:
            return None
        return dict(state)

    async def health_check(self, provider_name: str | None = None) -> dict[str, Any]:
        if provider_name:
            return await self._manager.health_check(provider_name)
        return await self._manager.health_check_all()
