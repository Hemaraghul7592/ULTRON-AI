from __future__ import annotations

from collections.abc import Callable, Coroutine  # noqa: TC003
from datetime import UTC, datetime
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


class Reminder:
    def __init__(
        self,
        reminder_id: str,
        title: str,
        message: str,
        remind_at: datetime,
        recurring: str | None = None,
        callback: Callable[..., Coroutine[Any, Any, Any]] | None = None,
    ) -> None:
        self.reminder_id = reminder_id
        self.title = title
        self.message = message
        self.remind_at = remind_at
        self.recurring = recurring
        self.callback = callback
        self.triggered: bool = False


class ReminderEngine:
    def __init__(self) -> None:
        self._reminders: dict[str, Reminder] = {}
        self._on_trigger: Callable[..., Coroutine[Any, Any, Any]] | None = None

    def set_trigger_callback(
        self,
        callback: Callable[..., Coroutine[Any, Any, Any]],
    ) -> None:
        self._on_trigger = callback

    def add_reminder(
        self,
        reminder_id: str,
        title: str,
        message: str,
        remind_at: datetime,
        recurring: str | None = None,
    ) -> Reminder:
        reminder = Reminder(
            reminder_id=reminder_id,
            title=title,
            message=message,
            remind_at=remind_at,
            recurring=recurring,
        )
        self._reminders[reminder_id] = reminder
        logger.info(
            "reminder_added",
            reminder_id=reminder_id,
            title=title,
            remind_at=remind_at.isoformat(),
        )
        return reminder

    def remove_reminder(self, reminder_id: str) -> bool:
        return self._reminders.pop(reminder_id, None) is not None

    async def check_reminders(self) -> list[Reminder]:
        now = datetime.now(UTC)
        triggered: list[Reminder] = []

        for reminder in self._reminders.values():
            if reminder.triggered:
                continue
            if reminder.remind_at <= now:
                triggered.append(reminder)
                reminder.triggered = True

                if self._on_trigger:
                    try:
                        await self._on_trigger(reminder)
                    except Exception as e:
                        logger.error(
                            "reminder_callback_failed",
                            reminder_id=reminder.reminder_id,
                            error=str(e),
                        )
                logger.info(
                    "reminder_triggered",
                    reminder_id=reminder.reminder_id,
                    title=reminder.title,
                )

        for reminder in triggered:
            if reminder.recurring:
                reminder.remind_at = self._calculate_next(reminder)
                reminder.triggered = False
            else:
                self._reminders.pop(reminder.reminder_id, None)

        return triggered

    def _calculate_next(self, reminder: Reminder) -> datetime:
        from datetime import timedelta

        now = datetime.now(UTC)
        if reminder.recurring == "daily":
            return now + timedelta(days=1)
        if reminder.recurring == "weekly":
            return now + timedelta(weeks=1)
        if reminder.recurring == "hourly":
            return now + timedelta(hours=1)
        return now + timedelta(days=1)

    def get_pending(self) -> list[dict[str, Any]]:
        return [
            {
                "reminder_id": r.reminder_id,
                "title": r.title,
                "message": r.message,
                "remind_at": r.remind_at.isoformat(),
                "recurring": r.recurring,
                "triggered": r.triggered,
            }
            for r in self._reminders.values()
            if not r.triggered
        ]

    def get_all(self) -> list[dict[str, Any]]:
        return [
            {
                "reminder_id": r.reminder_id,
                "title": r.title,
                "message": r.message,
                "remind_at": r.remind_at.isoformat(),
                "recurring": r.recurring,
                "triggered": r.triggered,
            }
            for r in self._reminders.values()
        ]
