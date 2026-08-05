from __future__ import annotations

import logging
from collections import deque
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.operations.incidents.domain.events import IncidentDomainEvent

logger = logging.getLogger(__name__)

_MAX_EVENTS = 500


class InMemoryInvestigationPublisher:
    def __init__(self, max_events: int = _MAX_EVENTS) -> None:
        self._events: deque[IncidentDomainEvent] = deque(maxlen=max_events)

    async def publish(self, event: IncidentDomainEvent) -> None:
        self._events.append(event)
        logger.info("incident_event_published", extra={"event_type": event.event_type})

    @property
    def events(self) -> list[IncidentDomainEvent]:
        return list(self._events)

    def clear(self) -> None:
        self._events.clear()
