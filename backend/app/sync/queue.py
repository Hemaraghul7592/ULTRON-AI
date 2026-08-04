from __future__ import annotations

import asyncio
import time
import uuid
from collections.abc import Callable  # noqa: TC003
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)

DEFAULT_MAX_RETRIES = 3
DEFAULT_BASE_DELAY = 1.0
DEFAULT_MAX_DELAY = 60.0


class QueueItem:
    def __init__(
        self,
        item_id: str,
        operation: Callable[..., Any],
        args: tuple = (),
        kwargs: dict | None = None,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> None:
        self.id = item_id
        self.operation = operation
        self.args = args
        self.kwargs = kwargs or {}
        self.max_retries = max_retries
        self.attempts = 0
        self.status = "pending"
        self.result: Any = None
        self.error: str = ""
        self.created_at = time.time()
        self.last_attempt: float = 0.0

    def can_retry(self) -> bool:
        return self.attempts < self.max_retries

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "attempts": self.attempts,
            "max_retries": self.max_retries,
            "status": self.status,
            "error": self.error,
        }


class SyncQueue:
    def __init__(
        self,
        max_retries: int = DEFAULT_MAX_RETRIES,
        base_delay: float = DEFAULT_BASE_DELAY,
        max_delay: float = DEFAULT_MAX_DELAY,
    ) -> None:
        self._items: dict[str, QueueItem] = {}
        self._order: list[str] = []
        self._max_retries = max_retries
        self._base_delay = base_delay
        self._max_delay = max_delay
        self._running = False

    def enqueue(
        self,
        operation: Callable[..., Any],
        *args: Any,
        max_retries: int | None = None,
        **kwargs: Any,
    ) -> str:
        item_id = str(uuid.uuid4())
        item = QueueItem(
            item_id=item_id,
            operation=operation,
            args=args,
            kwargs=kwargs,
            max_retries=max_retries if max_retries is not None else self._max_retries,
        )
        self._items[item_id] = item
        self._order.append(item_id)
        logger.debug("queue_enqueued", item_id=item_id)
        return item_id

    async def process_all(self) -> dict[str, Any]:
        results: dict[str, Any] = {"completed": 0, "failed": 0, "items": {}}
        self._running = True

        for item_id in list(self._order):
            if not self._running:
                break
            item = self._items.get(item_id)
            if item is None or item.status == "completed":
                continue
            await self._process_item(item)
            results["items"][item_id] = item.to_dict()
            if item.status == "completed":
                results["completed"] += 1
            else:
                results["failed"] += 1

        self._running = False
        return results

    async def process_one(self, item_id: str) -> QueueItem | None:
        item = self._items.get(item_id)
        if item is None:
            return None
        await self._process_item(item)
        return item

    async def _process_item(self, item: QueueItem) -> None:
        while item.can_retry() and item.status != "completed":
            item.attempts += 1
            item.last_attempt = time.time()
            item.status = "in_progress"

            try:
                if asyncio.iscoroutinefunction(item.operation):
                    item.result = await item.operation(*item.args, **item.kwargs)
                else:
                    item.result = item.operation(*item.args, **item.kwargs)
                item.status = "completed"
                item.error = ""
                logger.debug("queue_item_completed", item_id=item.id, attempts=item.attempts)
            except Exception as e:
                item.error = str(e)
                if item.can_retry():
                    delay = self._calculate_delay(item.attempts)
                    logger.warning(
                        "queue_item_retry",
                        item_id=item.id,
                        attempt=item.attempts,
                        delay=delay,
                        error=str(e),
                    )
                    await asyncio.sleep(delay)
                else:
                    item.status = "failed"
                    logger.error(
                        "queue_item_failed",
                        item_id=item.id,
                        attempts=item.attempts,
                        error=str(e),
                    )

    def _calculate_delay(self, attempt: int) -> float:
        delay = self._base_delay * (2 ** (attempt - 1))
        return min(delay, self._max_delay)

    def cancel(self, item_id: str) -> bool:
        item = self._items.get(item_id)
        if item:
            item.status = "failed"
            item.error = "cancelled"
            return True
        return False

    def cancel_all(self) -> None:
        self._running = False
        for item in self._items.values():
            if item.status in ("pending", "in_progress"):
                item.status = "failed"
                item.error = "cancelled"

    def get_status(self, item_id: str) -> dict[str, Any] | None:
        item = self._items.get(item_id)
        if item is None:
            return None
        return item.to_dict()

    def get_all_statuses(self) -> list[dict[str, Any]]:
        return [item.to_dict() for item in self._items.values()]

    def get_stats(self) -> dict[str, Any]:
        pending = sum(1 for i in self._items.values() if i.status == "pending")
        completed = sum(1 for i in self._items.values() if i.status == "completed")
        failed = sum(1 for i in self._items.values() if i.status == "failed")
        return {
            "total": len(self._items),
            "pending": pending,
            "completed": completed,
            "failed": failed,
        }

    def clear(self) -> None:
        self._items.clear()
        self._order.clear()
