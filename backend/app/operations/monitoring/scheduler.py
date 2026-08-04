from __future__ import annotations

import asyncio
import contextlib
import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

    from app.operations.domain.models import HealthSnapshot
    from app.operations.monitoring.aggregator import HealthAggregator

logger = logging.getLogger(__name__)


class MonitoringScheduler:
    def __init__(
        self,
        aggregator: HealthAggregator,
        interval_seconds: float = 30.0,
        on_snapshot: Callable[[HealthSnapshot], Any] | None = None,
    ) -> None:
        self._aggregator = aggregator
        self._interval = interval_seconds
        self._on_snapshot = on_snapshot
        self._task: asyncio.Task[None] | None = None
        self._running = False
        self._latest_snapshot: HealthSnapshot | None = None

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def interval(self) -> float:
        return self._interval

    @interval.setter
    def interval(self, value: float) -> None:
        self._interval = value

    @property
    def latest_snapshot(self) -> HealthSnapshot | None:
        return self._latest_snapshot

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("monitoring_scheduler_started", interval=self._interval)

    async def stop(self) -> None:
        if not self._running:
            return
        self._running = False
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
        self._task = None
        logger.info("monitoring_scheduler_stopped")

    async def run_once(self) -> HealthSnapshot:
        snapshot = await self._aggregator.collect()
        self._latest_snapshot = snapshot
        if self._on_snapshot:
            try:
                result = self._on_snapshot(snapshot)
                if asyncio.iscoroutine(result):
                    await result
            except Exception:  # noqa: BLE001
                logger.exception("snapshot_callback_failed")
        return snapshot

    async def _run_loop(self) -> None:
        try:
            await self.run_once()
        except Exception:  # noqa: BLE001
            logger.exception("initial_monitoring_run_failed")

        while self._running:
            try:
                await asyncio.sleep(self._interval)
                if not self._running:
                    break
                await self.run_once()
            except asyncio.CancelledError:
                break
            except Exception:  # noqa: BLE001
                logger.exception("monitoring_cycle_failed")
