from __future__ import annotations

import time
from typing import Any

from app.core.logging import get_logger
from app.sync.errors import ProviderUnavailableError
from app.sync.interface import SyncChange, SyncProvider, SyncResult, SyncState
from app.sync.models import change_key, is_older
from app.sync.queue import SyncQueue
from app.sync.resolver import ConflictResolver, ResolutionStrategy

logger = get_logger(__name__)


class SyncManager:
    def __init__(
        self,
        conflict_strategy: str = ResolutionStrategy.LAST_WRITE_WINS,
        queue_retries: int = 3,
    ) -> None:
        self._providers: dict[str, SyncProvider] = {}
        self._resolver = ConflictResolver(strategy=conflict_strategy)
        self._queue = SyncQueue(max_retries=queue_retries)
        self._states: dict[str, SyncState] = {}
        self._changes: dict[str, list[SyncChange]] = {}

    @property
    def queue(self) -> SyncQueue:
        return self._queue

    @property
    def resolver(self) -> ConflictResolver:
        return self._resolver

    def register_provider(self, provider: SyncProvider) -> None:
        self._providers[provider.name] = provider
        self._states[provider.name] = SyncState(
            last_sync_version=0,
            pending_count=0,
            provider=provider.name,
        )
        logger.info("sync_provider_registered", provider=provider.name)

    def unregister_provider(self, name: str) -> bool:
        if name in self._providers:
            del self._providers[name]
            self._states.pop(name, None)
            self._changes.pop(name, None)
            logger.info("sync_provider_unregistered", provider=name)
            return True
        return False

    def get_provider(self, name: str) -> SyncProvider | None:
        return self._providers.get(name)

    def list_providers(self) -> list[str]:
        return list(self._providers.keys())

    async def push(self, provider_name: str, changes: list[SyncChange]) -> SyncResult:
        provider = self._get_provider(provider_name)
        try:
            return await provider.push(changes)
        except Exception as e:
            logger.error("sync_push_failed", provider=provider_name, error=str(e))
            raise

    async def pull(self, provider_name: str, since: str | None = None) -> list[SyncChange]:
        provider = self._get_provider(provider_name)
        try:
            changes = await provider.pull(since)
            state = self._states.get(provider_name)
            if state:
                state["last_sync_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                state["last_sync_version"] = max(
                    state.get("last_sync_version", 0),
                    max((c.get("version", 0) for c in changes), default=0),
                )
            return changes
        except Exception as e:
            logger.error("sync_pull_failed", provider=provider_name, error=str(e))
            raise

    async def sync(self, provider_name: str) -> SyncResult:
        provider = self._get_provider(provider_name)
        local_changes = self._changes.get(provider_name, [])
        try:
            remote_changes = await provider.pull()
        except Exception as e:
            raise ProviderUnavailableError(
                message=str(e),
                provider=provider_name,
                original_error=e,
            ) from e

        resolved: list[SyncChange] = []
        for lc in local_changes:
            matched = False
            for rc in remote_changes:
                if change_key(lc) == change_key(rc) and is_older(lc, rc):
                    resolved_change, conflict = self._resolver.resolve(lc, rc)
                    resolved.append(resolved_change)
                    matched = True
                    break
            if not matched:
                resolved.append(lc)

        for rc in remote_changes:
            if not any(change_key(rc) == change_key(r) for r in resolved):
                resolved.append(rc)

        result = await provider.push(resolved)
        self._changes[provider_name] = []
        return result

    def track_change(self, provider_name: str, change: SyncChange) -> None:
        if provider_name not in self._changes:
            self._changes[provider_name] = []
        existing = [
            c for c in self._changes.get(provider_name, []) if change_key(c) == change_key(change)
        ]
        if existing and is_older(existing[0], change):
            self._changes[provider_name] = [
                c
                for c in self._changes.get(provider_name, [])
                if change_key(c) != change_key(change)
            ]
        self._changes.setdefault(provider_name, []).append(change)

    def get_tracked_changes(self, provider_name: str) -> list[SyncChange]:
        return list(self._changes.get(provider_name, []))

    def get_state(self, provider_name: str) -> SyncState | None:
        return self._states.get(provider_name)

    def clear_tracked(self, provider_name: str) -> None:
        self._changes.pop(provider_name, None)

    async def health_check(self, provider_name: str) -> dict[str, Any]:
        provider = self._get_provider(provider_name)
        return await provider.health_check()

    async def health_check_all(self) -> dict[str, Any]:
        results: dict[str, Any] = {}
        for name, provider in self._providers.items():
            try:
                results[name] = await provider.health_check()
            except Exception as e:
                results[name] = {"status": "error", "error": str(e)}
        return {"providers": results, "queue": self._queue.get_stats()}

    def _get_provider(self, name: str) -> SyncProvider:
        provider = self._providers.get(name)
        if provider is None:
            raise ProviderUnavailableError(message=f"Provider '{name}' not found", provider=name)
        return provider
