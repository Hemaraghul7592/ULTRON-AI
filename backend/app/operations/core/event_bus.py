from __future__ import annotations

import asyncio
import threading
from collections import defaultdict
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Protocol, TypeVar
from uuid import UUID, uuid4

from app.operations.domain.events import DomainEvent

TEvent = TypeVar("TEvent", bound=DomainEvent)
EventHandler = Callable[[TEvent], Awaitable[None]]


@dataclass(frozen=True, slots=True)
class EventSubscription:
    subscription_id: UUID
    event_type: type[DomainEvent]


class EventBus(Protocol):
    def subscribe(
        self, event_type: type[TEvent], handler: EventHandler[TEvent],
    ) -> EventSubscription: ...

    def unsubscribe(self, subscription: EventSubscription) -> None: ...

    async def publish(self, event: DomainEvent) -> None: ...


class InProcessEventBus:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._handlers: dict[
            type[DomainEvent], dict[UUID, Callable[[DomainEvent], Awaitable[None]]],
        ] = defaultdict(dict)

    def subscribe(
        self, event_type: type[TEvent], handler: EventHandler[TEvent],
    ) -> EventSubscription:
        subscription = EventSubscription(subscription_id=uuid4(), event_type=event_type)

        async def _wrapped(event: DomainEvent) -> None:
            await handler(event)

        # Synchronous registration is safe because the mapping is only mutated here.
        with self._lock:
            self._handlers[event_type][subscription.subscription_id] = _wrapped
        return subscription

    def unsubscribe(self, subscription: EventSubscription) -> None:
        with self._lock:
            handlers = self._handlers.get(subscription.event_type)
            if handlers is None:
                return
            handlers.pop(subscription.subscription_id, None)
            if not handlers:
                self._handlers.pop(subscription.event_type, None)

    async def publish(self, event: DomainEvent) -> None:
        handlers: list[Callable[[DomainEvent], Awaitable[None]]] = []
        with self._lock:
            for event_type, subscribers in self._handlers.items():
                if issubclass(type(event), event_type):
                    handlers.extend(subscribers.values())
        if not handlers:
            return
        await asyncio.gather(*(handler(event) for handler in handlers))
