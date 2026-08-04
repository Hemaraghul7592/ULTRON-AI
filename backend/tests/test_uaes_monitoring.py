from __future__ import annotations

import asyncio

import pytest

from app.operations.domain.enums import (
    ComponentType,
    EnvironmentType,
    EventType,
    HealthStatus,
)
from app.operations.domain.events import (
    ComponentStatus,
    HealthCheckCompleted,
    HealthCheckStarted,
)
from app.operations.domain.models import ComponentHealth, HealthSnapshot
from app.operations.monitoring.aggregator import HealthAggregator, _worst_status
from app.operations.monitoring.factory import create_monitors
from app.operations.monitoring.monitors.base import (
    _build_health,
    _critical,
    _healthy,
    _not_configured,
    _offline,
    _warning,
)


class _StubMonitor:
    component_type = ComponentType.BACKEND
    component_name = "stub"

    def __init__(self, environment, status, score, message="stub"):
        self.environment = environment
        self._status = status
        self._score = score
        self._message = message

    async def check(self):
        return _build_health(
            self.component_type,
            self.component_name,
            self.environment,
            self._status,
            self._score,
            self._message,
        )


class TestHelperFunctions:
    def test_healthy(self):
        result = _healthy(ComponentType.BACKEND, "api", EnvironmentType.DEVELOPMENT)
        assert result.status == HealthStatus.HEALTHY
        assert result.score == 100.0

    def test_warning(self):
        result = _warning(ComponentType.CPU, "cpu", EnvironmentType.DEVELOPMENT, "high", 50.0)
        assert result.status == HealthStatus.WARNING
        assert result.score == 50.0

    def test_critical(self):
        result = _critical(ComponentType.DATABASE, "db", EnvironmentType.PRODUCTION, "down", 10.0)
        assert result.status == HealthStatus.CRITICAL
        assert result.score == 10.0

    def test_offline(self):
        result = _offline(ComponentType.REDIS, "cache", EnvironmentType.STAGING)
        assert result.status == HealthStatus.OFFLINE
        assert result.score == 0.0

    def test_not_configured(self):
        result = _not_configured(ComponentType.DOCKER, "docker", EnvironmentType.DEVELOPMENT)
        assert result.status == HealthStatus.NOT_CONFIGURED
        assert result.score == 0.0


class TestWorstStatus:
    def test_all_not_configured(self):
        assert (
            _worst_status([HealthStatus.NOT_CONFIGURED, HealthStatus.NOT_CONFIGURED])
            == HealthStatus.NOT_CONFIGURED
        )

    def test_critical_is_worst(self):
        statuses = [
            HealthStatus.HEALTHY,
            HealthStatus.WARNING,
            HealthStatus.CRITICAL,
            HealthStatus.NOT_CONFIGURED,
        ]
        assert _worst_status(statuses) == HealthStatus.CRITICAL

    def test_offline_beats_warning(self):
        statuses = [HealthStatus.WARNING, HealthStatus.OFFLINE, HealthStatus.NOT_CONFIGURED]
        assert _worst_status(statuses) == HealthStatus.OFFLINE

    def test_ignores_not_configured(self):
        statuses = [HealthStatus.HEALTHY, HealthStatus.NOT_CONFIGURED, HealthStatus.NOT_CONFIGURED]
        assert _worst_status(statuses) == HealthStatus.HEALTHY

    def test_empty_list(self):
        assert _worst_status([]) == HealthStatus.NOT_CONFIGURED


class TestHealthAggregator:
    @pytest.mark.asyncio
    async def test_all_healthy(self):
        monitors = [
            _StubMonitor(EnvironmentType.DEVELOPMENT, HealthStatus.HEALTHY, 100.0),
            _StubMonitor(EnvironmentType.DEVELOPMENT, HealthStatus.HEALTHY, 100.0),
        ]
        agg = HealthAggregator(monitors)
        snapshot = await agg.collect()
        assert snapshot.overall_status == HealthStatus.HEALTHY
        assert snapshot.overall_score == 100.0
        assert len(snapshot.components) == 2

    @pytest.mark.asyncio
    async def test_mixed_status(self):
        monitors = [
            _StubMonitor(EnvironmentType.DEVELOPMENT, HealthStatus.HEALTHY, 100.0),
            _StubMonitor(EnvironmentType.DEVELOPMENT, HealthStatus.CRITICAL, 0.0),
        ]
        agg = HealthAggregator(monitors)
        snapshot = await agg.collect()
        assert snapshot.overall_status == HealthStatus.CRITICAL
        assert snapshot.overall_score == 50.0

    @pytest.mark.asyncio
    async def test_not_configured_ignored_in_score(self):
        monitors = [
            _StubMonitor(EnvironmentType.DEVELOPMENT, HealthStatus.HEALTHY, 100.0),
            _StubMonitor(EnvironmentType.DEVELOPMENT, HealthStatus.NOT_CONFIGURED, 0.0),
        ]
        agg = HealthAggregator(monitors)
        snapshot = await agg.collect()
        assert snapshot.overall_status == HealthStatus.HEALTHY
        assert snapshot.overall_score == 100.0

    @pytest.mark.asyncio
    async def test_weighted_score(self):
        monitors = [
            _StubMonitor(EnvironmentType.DEVELOPMENT, HealthStatus.HEALTHY, 100.0),
            _StubMonitor(EnvironmentType.DEVELOPMENT, HealthStatus.WARNING, 50.0),
        ]
        agg = HealthAggregator(monitors)
        snapshot = await agg.collect()
        assert snapshot.overall_status == HealthStatus.WARNING
        assert snapshot.overall_score > 50.0

    @pytest.mark.asyncio
    async def test_summarize(self):
        monitors = [
            _StubMonitor(EnvironmentType.DEVELOPMENT, HealthStatus.HEALTHY, 100.0),
            _StubMonitor(EnvironmentType.DEVELOPMENT, HealthStatus.CRITICAL, 0.0),
            _StubMonitor(EnvironmentType.DEVELOPMENT, HealthStatus.NOT_CONFIGURED, 0.0),
        ]
        agg = HealthAggregator(monitors)
        snapshot = await agg.collect()
        summary = agg.summarize(snapshot)
        assert summary["total_components"] == 3
        assert summary["status_breakdown"]["healthy"] == 1
        assert summary["status_breakdown"]["critical"] == 1
        assert summary["status_breakdown"]["not_configured"] == 1

    def test_component_weights(self):
        monitors = [
            _StubMonitor(EnvironmentType.DEVELOPMENT, HealthStatus.HEALTHY, 100.0),
        ]
        agg = HealthAggregator(monitors)
        weights = agg.component_weights()
        assert weights[ComponentType.BACKEND] == 2.0

    def test_component_weights_disk_uses_default(self):
        class _DiskStub:
            component_type = ComponentType.DISK
            component_name = "disk"

        agg = HealthAggregator([])
        agg._monitors = [_DiskStub()]  # noqa: SLF001
        weights = agg.component_weights()
        assert weights[ComponentType.DISK] == 1.0


class TestFactory:
    def test_create_monitors_returns_all_types(self):
        monitors = create_monitors()
        types = {m.component_type for m in monitors}
        assert ComponentType.DATABASE in types
        assert ComponentType.REDIS in types
        assert ComponentType.BACKEND in types
        assert ComponentType.DOCKER in types
        assert ComponentType.GITHUB_ACTIONS in types
        assert ComponentType.CPU in types
        assert ComponentType.MEMORY in types
        assert ComponentType.DISK in types
        assert ComponentType.NETWORK in types

    def test_create_monitors_with_environment(self):
        monitors = create_monitors(environment=EnvironmentType.PRODUCTION)
        for m in monitors:
            assert m.environment == EnvironmentType.PRODUCTION


class TestEvents:
    def test_health_check_started_event(self):
        event = HealthCheckStarted(
            component_type=ComponentType.DATABASE,
            component_name="postgres",
        )
        assert event.event_type == EventType.HEALTH_CHECK_STARTED
        assert event.component_type == ComponentType.DATABASE
        assert event.component_name == "postgres"

    def test_health_check_completed_event(self):
        event = HealthCheckCompleted(
            component_type=ComponentType.REDIS,
            component_name="cache",
            status=HealthStatus.HEALTHY,
            score=100.0,
            message="all good",
        )
        assert event.event_type == EventType.HEALTH_CHECK_COMPLETED
        assert event.score == 100.0

    def test_component_status_event(self):
        component = _build_health(
            ComponentType.API,
            "api-gateway",
            EnvironmentType.PRODUCTION,
            HealthStatus.WARNING,
            75.0,
            "slow",
            {"latency_ms": "500"},
        )
        event = ComponentStatus(
            event_type=EventType.COMPONENT_WARNING,
            component=component,
        )
        assert event.event_type == EventType.COMPONENT_WARNING
        assert event.component.status == HealthStatus.WARNING


class TestMonitoringScheduler:
    @pytest.mark.asyncio
    async def test_scheduler_run_once(self):
        from app.operations.monitoring.scheduler import MonitoringScheduler

        snapshots = []

        async def on_snapshot(snapshot):
            snapshots.append(snapshot)

        monitors = [
            _StubMonitor(EnvironmentType.DEVELOPMENT, HealthStatus.HEALTHY, 100.0),
        ]
        aggregator = HealthAggregator(monitors)
        scheduler = MonitoringScheduler(
            aggregator=aggregator, interval_seconds=0.1, on_snapshot=on_snapshot
        )
        result = await scheduler.run_once()
        assert result is not None
        assert len(snapshots) == 1

    @pytest.mark.asyncio
    async def test_scheduler_start_stop(self):
        from app.operations.monitoring.scheduler import MonitoringScheduler

        monitors = [
            _StubMonitor(EnvironmentType.DEVELOPMENT, HealthStatus.HEALTHY, 100.0),
        ]
        aggregator = HealthAggregator(monitors)
        scheduler = MonitoringScheduler(aggregator=aggregator, interval_seconds=10.0)

        await scheduler.start()
        assert scheduler.is_running
        await asyncio.sleep(0.15)
        assert scheduler.latest_snapshot is not None

        await scheduler.stop()
        assert not scheduler.is_running

    @pytest.mark.asyncio
    async def test_scheduler_callback_exception_does_not_crash(self):
        from app.operations.monitoring.scheduler import MonitoringScheduler

        async def failing_callback(snapshot):
            raise RuntimeError("boom")

        monitors = [
            _StubMonitor(EnvironmentType.DEVELOPMENT, HealthStatus.HEALTHY, 100.0),
        ]
        aggregator = HealthAggregator(monitors)
        scheduler = MonitoringScheduler(
            aggregator=aggregator, interval_seconds=10.0, on_snapshot=failing_callback
        )
        result = await scheduler.run_once()
        assert result is not None


class TestMonitoringRepository:
    @pytest.mark.asyncio
    async def test_record_and_retrieve_snapshot(self):
        from app.core.database import get_session
        from app.operations.infrastructure.db.repositories import SQLAlchemyHealthRepository

        session_factory = get_session()
        async with session_factory() as session:
            repo = SQLAlchemyHealthRepository(session)
            snapshot = HealthSnapshot(
                snapshot_id="test-snapshot",
                environment=EnvironmentType.DEVELOPMENT,
                overall_status=HealthStatus.HEALTHY,
                overall_score=100.0,
                components=[
                    ComponentHealth(
                        component_id=ComponentType.DATABASE.value,
                        component_type=ComponentType.DATABASE,
                        component_name="db",
                        environment=EnvironmentType.DEVELOPMENT,
                        status=HealthStatus.HEALTHY,
                        score=100.0,
                        message="ok",
                    ),
                ],
            )
            await repo.record_snapshot(snapshot)
            latest = await repo.latest_snapshot()
            assert latest is not None
            assert latest.snapshot_id == "test-snapshot"
            assert latest.overall_status == HealthStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_list_snapshots(self):
        from app.core.database import get_session
        from app.operations.infrastructure.db.repositories import SQLAlchemyHealthRepository

        session_factory = get_session()
        async with session_factory() as session:
            repo = SQLAlchemyHealthRepository(session)

            for i in range(3):
                snapshot = HealthSnapshot(
                    snapshot_id=f"snap-{i}",
                    environment=EnvironmentType.DEVELOPMENT,
                    overall_status=HealthStatus.HEALTHY,
                    overall_score=100.0,
                    components=[],
                )
                await repo.record_snapshot(snapshot)

            snapshots = await repo.list_snapshots(limit=10)
            assert len(snapshots) == 3
