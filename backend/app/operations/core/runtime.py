from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.operations.core.event_bus import EventBus


@dataclass(slots=True)
class OperationsRuntime:
    event_bus: EventBus
    session_factory: async_sessionmaker[AsyncSession]
