from __future__ import annotations

import pytest

from app.sync.errors import (
    AuthenticationError,
    ConflictError,
    ProviderUnavailableError,
    QueueError,
    RetryExceededError,
    SyncError,
)
from app.sync.interface import (
    SyncAction,
)
from app.sync.manager import SyncManager
from app.sync.models import change_key, compute_checksum, is_older, make_change, merge_changes
from app.sync.providers.mock import MockSyncProvider
from app.sync.queue import SyncQueue
from app.sync.resolver import ConflictResolver, ResolutionStrategy
from app.sync.service import SyncService


class TestSyncModels:
    def test_compute_checksum(self) -> None:
        c = compute_checksum({"key": "value"})
        assert len(c) == 64

    def test_checksum_deterministic(self) -> None:
        a = compute_checksum({"a": 1})
        b = compute_checksum({"a": 1})
        assert a == b

    def test_make_change(self) -> None:
        change = make_change("memories", "abc", SyncAction.CREATE, {"content": "hi"}, version=2)
        assert change["entity_type"] == "memories"
        assert change["entity_id"] == "abc"
        assert change["action"] == SyncAction.CREATE
        assert change["version"] == 2
        assert len(change["checksum"]) == 64

    def test_change_key(self) -> None:
        c = make_change("memories", "id1", SyncAction.UPDATE, {})
        assert change_key(c) == "memories:id1"

    def test_is_older(self) -> None:
        a = make_change("t", "1", SyncAction.UPDATE, {}, version=1)
        b = make_change("t", "1", SyncAction.UPDATE, {}, version=2)
        assert is_older(a, b) is True
        assert is_older(b, a) is False

    def test_merge_changes_newer_remote_wins(self) -> None:
        local = [make_change("t", "1", SyncAction.UPDATE, {"x": 1}, version=1)]
        remote = [make_change("t", "1", SyncAction.UPDATE, {"x": 2}, version=2)]
        merged = merge_changes(local, remote)
        assert len(merged) == 1
        assert merged[0]["data"]["x"] == 2

    def test_merge_changes_local_kept_when_no_conflict(self) -> None:
        local = [make_change("t", "1", SyncAction.CREATE, {"a": 1})]
        remote = [make_change("t", "2", SyncAction.CREATE, {"b": 2})]
        merged = merge_changes(local, remote)
        assert len(merged) == 2


class TestConflictResolver:
    def test_last_write_wins_version(self) -> None:
        r = ConflictResolver(strategy=ResolutionStrategy.LAST_WRITE_WINS)
        local = make_change("t", "1", SyncAction.UPDATE, {"val": 1}, version=5)
        remote = make_change("t", "1", SyncAction.UPDATE, {"val": 2}, version=3)
        resolved, conflict = r.resolve(local, remote)
        assert resolved["version"] == 5
        assert conflict["resolution"] == "last_write_wins"
        assert r.has_conflicts() is True

    def test_last_write_wins_remote_higher(self) -> None:
        r = ConflictResolver(strategy=ResolutionStrategy.LAST_WRITE_WINS)
        local = make_change("t", "1", SyncAction.UPDATE, {}, version=2)
        remote = make_change("t", "1", SyncAction.UPDATE, {}, version=3)
        resolved, _ = r.resolve(local, remote)
        assert resolved["version"] == 3

    def test_timestamp_strategy(self) -> None:
        r = ConflictResolver(strategy=ResolutionStrategy.TIMESTAMP)
        local = make_change("t", "1", SyncAction.UPDATE, {}, version=1)
        remote = make_change("t", "1", SyncAction.UPDATE, {}, version=1)
        resolved, _ = r.resolve(local, remote)
        assert resolved is not None

    def test_provider_priority(self) -> None:
        r = ConflictResolver(strategy=ResolutionStrategy.PROVIDER_PRIORITY)
        local = make_change("t", "1", SyncAction.UPDATE, {"val": 1}, version=1)
        remote = make_change("t", "1", SyncAction.UPDATE, {"val": 2}, version=1)
        resolved, _ = r.resolve(local, remote)
        assert resolved["data"]["val"] == 2

    def test_manual_strategy(self) -> None:
        r = ConflictResolver(strategy=ResolutionStrategy.MANUAL)
        local = make_change("t", "1", SyncAction.UPDATE, {"val": 1}, version=1)
        remote = make_change("t", "1", SyncAction.UPDATE, {"val": 2}, version=1)
        resolved, conflict = r.resolve(local, remote)
        assert resolved["data"]["val"] == 1
        assert conflict["resolution"] == "manual_local"

    def test_clear_conflicts(self) -> None:
        r = ConflictResolver()
        r.resolve(
            make_change("t", "1", SyncAction.UPDATE, {}, version=1),
            make_change("t", "1", SyncAction.UPDATE, {}, version=2),
        )
        r.clear()
        assert r.has_conflicts() is False

    def test_switch_strategy(self) -> None:
        r = ConflictResolver(strategy=ResolutionStrategy.LAST_WRITE_WINS)
        r.strategy = ResolutionStrategy.TIMESTAMP
        assert r.strategy == "timestamp"

    def test_conflict_info(self) -> None:
        r = ConflictResolver()
        local = make_change("memories", "abc", SyncAction.UPDATE, {"content": "local"}, version=3)
        remote = make_change("memories", "abc", SyncAction.UPDATE, {"content": "remote"}, version=5)
        _, conflict = r.resolve(local, remote)
        assert conflict["entity_type"] == "memories"
        assert conflict["entity_id"] == "abc"
        assert conflict["local_version"] == 3
        assert conflict["remote_version"] == 5
        assert conflict["local_data"]["content"] == "local"


class TestSyncQueue:
    @pytest.fixture
    def queue(self) -> SyncQueue:
        return SyncQueue(max_retries=2, base_delay=0.01)

    def test_enqueue(self, queue: SyncQueue) -> None:
        item_id = queue.enqueue(lambda: "ok")
        assert len(queue._items) == 1
        assert queue._items[item_id].status == "pending"

    @pytest.mark.asyncio
    async def test_process_all_completes(self, queue: SyncQueue) -> None:
        results = []
        queue.enqueue(lambda r=results: r.append("done"))
        await queue.process_all()
        assert results == ["done"]

    @pytest.mark.asyncio
    async def test_retry_on_failure(self, queue: SyncQueue) -> None:
        call_count = []

        def fail_twice() -> str:
            call_count.append(1)
            if len(call_count) < 3:
                raise ValueError("fail")
            return "ok"

        queue.enqueue(fail_twice, max_retries=3)
        await queue.process_all()
        assert call_count == [1, 1, 1]
        assert len(queue._items) == 1

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, queue: SyncQueue) -> None:
        def always_fail() -> None:
            raise ValueError("fail")

        item_id = queue.enqueue(always_fail, max_retries=1)
        await queue.process_all()
        item = queue._items[item_id]
        assert item.status == "failed"
        assert item.attempts == 1

    @pytest.mark.asyncio
    async def test_cancel(self, queue: SyncQueue) -> None:
        item_id = queue.enqueue(lambda: "ok")
        assert queue.cancel(item_id) is True
        assert queue._items[item_id].status == "failed"
        assert queue.cancel("nonexistent") is False

    def test_cancel_all(self, queue: SyncQueue) -> None:
        queue.enqueue(lambda: "ok")
        queue.enqueue(lambda: "ok")
        queue.cancel_all()
        for item in queue._items.values():
            assert item.status == "failed"

    def test_get_status(self, queue: SyncQueue) -> None:
        item_id = queue.enqueue(lambda: "ok")
        status = queue.get_status(item_id)
        assert status is not None
        assert status["status"] == "pending"
        assert queue.get_status("nope") is None

    def test_get_all_statuses(self, queue: SyncQueue) -> None:
        queue.enqueue(lambda: "ok")
        queue.enqueue(lambda: "ok")
        assert len(queue.get_all_statuses()) == 2

    def test_get_stats(self, queue: SyncQueue) -> None:
        queue.enqueue(lambda: "ok")
        stats = queue.get_stats()
        assert stats["total"] == 1
        assert stats["pending"] == 1
        assert stats["completed"] == 0

    @pytest.mark.asyncio
    async def test_clear(self, queue: SyncQueue) -> None:
        queue.enqueue(lambda: "ok")
        queue.clear()
        assert len(queue._items) == 0

    @pytest.mark.asyncio
    async def test_process_one(self, queue: SyncQueue) -> None:
        item_id = queue.enqueue(lambda: "done")
        item = await queue.process_one(item_id)
        assert item is not None
        assert item.status == "completed"


class TestSyncManager:
    @pytest.fixture
    def provider(self) -> MockSyncProvider:
        return MockSyncProvider(name="test_provider")

    @pytest.fixture
    def manager(self) -> SyncManager:
        return SyncManager()

    @pytest.mark.asyncio
    async def test_register_provider(
        self, manager: SyncManager, provider: MockSyncProvider,
    ) -> None:
        manager.register_provider(provider)
        assert manager.get_provider("test_provider") is provider

    def test_unregister_provider(self, manager: SyncManager, provider: MockSyncProvider) -> None:
        manager.register_provider(provider)
        assert manager.unregister_provider("test_provider") is True
        assert manager.get_provider("test_provider") is None

    def test_list_providers(self, manager: SyncManager, provider: MockSyncProvider) -> None:
        manager.register_provider(provider)
        assert "test_provider" in manager.list_providers()

    @pytest.mark.asyncio
    async def test_push(self, manager: SyncManager, provider: MockSyncProvider) -> None:
        manager.register_provider(provider)
        changes = [make_change("t", "1", SyncAction.CREATE, {"val": 1})]
        result = await manager.push("test_provider", changes)
        assert result["status"] == "completed"
        assert result["changes_processed"] == 1

    @pytest.mark.asyncio
    async def test_pull(self, manager: SyncManager, provider: MockSyncProvider) -> None:
        provider.set_pull_changes([make_change("t", "1", SyncAction.CREATE, {"val": 1})])
        manager.register_provider(provider)
        changes = await manager.pull("test_provider")
        assert len(changes) == 1

    @pytest.mark.asyncio
    async def test_sync(self, manager: SyncManager, provider: MockSyncProvider) -> None:
        provider.set_pull_changes([make_change("t", "1", SyncAction.UPDATE, {"val": 1})])
        manager.register_provider(provider)
        manager.track_change(
            "test_provider", make_change("t", "1", SyncAction.CREATE, {"val": 0}, version=1),
        )
        result = await manager.sync("test_provider")
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_track_change(self, manager: SyncManager, provider: MockSyncProvider) -> None:
        manager.register_provider(provider)
        manager.track_change("test_provider", make_change("t", "1", SyncAction.CREATE, {}))
        assert len(manager.get_tracked_changes("test_provider")) == 1

    @pytest.mark.asyncio
    async def test_get_state(self, manager: SyncManager, provider: MockSyncProvider) -> None:
        manager.register_provider(provider)
        state = manager.get_state("test_provider")
        assert state is not None
        assert state["provider"] == "test_provider"

    @pytest.mark.asyncio
    async def test_health_check(self, manager: SyncManager, provider: MockSyncProvider) -> None:
        manager.register_provider(provider)
        hc = await manager.health_check("test_provider")
        assert hc["status"] == "available"

    @pytest.mark.asyncio
    async def test_health_check_all(self, manager: SyncManager, provider: MockSyncProvider) -> None:
        manager.register_provider(provider)
        result = await manager.health_check_all()
        assert "providers" in result
        assert "test_provider" in result["providers"]
        assert "queue" in result

    @pytest.mark.asyncio
    async def test_push_fails_with_unknown_provider(self, manager: SyncManager) -> None:
        with pytest.raises(ProviderUnavailableError):
            await manager.push("nobody", [])

    @pytest.mark.asyncio
    async def test_push_passthrough_error(self, manager: SyncManager) -> None:
        p = MockSyncProvider(name="bad", should_fail_push=True)
        manager.register_provider(p)
        with pytest.raises(RuntimeError, match="mock error"):
            await manager.push("bad", [])

    def test_clear_tracked(self, manager: SyncManager, provider: MockSyncProvider) -> None:
        manager.register_provider(provider)
        manager.track_change("test_provider", make_change("t", "1", SyncAction.CREATE, {}))
        manager.clear_tracked("test_provider")
        assert len(manager.get_tracked_changes("test_provider")) == 0


class TestSyncService:
    @pytest.fixture
    def service(self) -> SyncService:
        return SyncService()

    @pytest.fixture
    def provider(self) -> MockSyncProvider:
        return MockSyncProvider(name="mock")

    def test_register_provider(self, service: SyncService, provider: MockSyncProvider) -> None:
        service.register_provider(provider)
        assert service.get_provider("mock") is provider

    @pytest.mark.asyncio
    async def test_push(self, service: SyncService, provider: MockSyncProvider) -> None:
        service.register_provider(provider)
        result = await service.push("mock", [make_change("t", "1", SyncAction.CREATE, {})])
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_pull(self, service: SyncService, provider: MockSyncProvider) -> None:
        provider.set_pull_changes([make_change("t", "1", SyncAction.CREATE, {})])
        service.register_provider(provider)
        changes = await service.pull("mock")
        assert len(changes) == 1

    @pytest.mark.asyncio
    async def test_sync(self, service: SyncService, provider: MockSyncProvider) -> None:
        service.register_provider(provider)
        result = await service.sync("mock")
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_health_check(self, service: SyncService, provider: MockSyncProvider) -> None:
        service.register_provider(provider)
        result = await service.health_check()
        assert "providers" in result
        assert "mock" in result["providers"]

    @pytest.mark.asyncio
    async def test_health_check_specific(
        self, service: SyncService, provider: MockSyncProvider,
    ) -> None:
        service.register_provider(provider)
        result = await service.health_check("mock")
        assert result["status"] == "available"

    @pytest.mark.asyncio
    async def test_list_providers(self, service: SyncService, provider: MockSyncProvider) -> None:
        service.register_provider(provider)
        assert "mock" in service.list_providers()

    @pytest.mark.asyncio
    async def test_unregister(self, service: SyncService, provider: MockSyncProvider) -> None:
        service.register_provider(provider)
        assert service.unregister_provider("mock") is True
        assert service.get_provider("mock") is None

    @pytest.mark.asyncio
    async def test_track_change(self, service: SyncService, provider: MockSyncProvider) -> None:
        service.register_provider(provider)
        service.track_change("mock", make_change("t", "1", SyncAction.CREATE, {}))
        changes = service.get_tracked_changes("mock")
        assert len(changes) == 1

    @pytest.mark.asyncio
    async def test_get_sync_state(self, service: SyncService, provider: MockSyncProvider) -> None:
        service.register_provider(provider)
        state = service.get_sync_state("mock")
        assert state is not None
        assert state["provider"] == "mock"


class TestSyncErrors:
    def test_error_hierarchy(self) -> None:
        e1 = ProviderUnavailableError("down")
        assert isinstance(e1, SyncError)
        e2 = ConflictError("conflict")
        assert isinstance(e2, SyncError)
        e3 = RetryExceededError("retry")
        assert isinstance(e3, SyncError)
        e4 = AuthenticationError("auth")
        assert isinstance(e4, SyncError)
        e5 = QueueError("queue")
        assert isinstance(e5, SyncError)

    def test_conflict_error_carries_conflict(self) -> None:
        e = ConflictError("msg", provider="p1", conflict={"type": "test"})
        assert e.conflict["type"] == "test"
        assert e.provider == "p1"


class TestMockProvider:
    @pytest.mark.asyncio
    async def test_push(self) -> None:
        p = MockSyncProvider()
        result = await p.push([make_change("t", "1", SyncAction.CREATE, {})])
        assert result["changes_processed"] == 1

    @pytest.mark.asyncio
    async def test_pull(self) -> None:
        p = MockSyncProvider(pull_changes=[make_change("t", "1", SyncAction.CREATE, {})])
        changes = await p.pull()
        assert len(changes) == 1

    @pytest.mark.asyncio
    async def test_fail_push(self) -> None:
        p = MockSyncProvider(should_fail_push=True)
        with pytest.raises(RuntimeError):
            await p.push([])

    @pytest.mark.asyncio
    async def test_fail_pull(self) -> None:
        p = MockSyncProvider(should_fail_pull=True)
        with pytest.raises(RuntimeError):
            await p.pull()

    def test_pushed_tracks_all(self) -> None:
        p = MockSyncProvider()
        import asyncio

        changes = [make_change("t", "1", SyncAction.CREATE, {})]
        asyncio.run(p.push(changes))
        assert len(p.pushed) == 1

    @pytest.mark.asyncio
    async def test_set_pull_changes(self) -> None:
        p = MockSyncProvider()
        p.set_pull_changes([make_change("t", "1", SyncAction.CREATE, {})])
        changes = await p.pull()
        assert len(changes) == 1

    @pytest.mark.asyncio
    async def test_health_check(self) -> None:
        p = MockSyncProvider()
        hc = await p.health_check()
        assert hc["status"] == "available"

    @pytest.mark.asyncio
    async def test_validate(self) -> None:
        p = MockSyncProvider()
        assert await p.validate() is True

    @pytest.mark.asyncio
    async def test_metadata(self) -> None:
        p = MockSyncProvider()
        meta = p.metadata()
        assert meta["name"] == "mock"
        assert "version" in meta
