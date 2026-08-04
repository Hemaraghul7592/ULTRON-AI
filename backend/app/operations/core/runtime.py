from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker  # noqa: TC002

from app.operations.core.event_bus import EventBus  # noqa: TC001


@dataclass(slots=True)
class OperationsRuntime:
    event_bus: EventBus
    session_factory: async_sessionmaker[AsyncSession]
