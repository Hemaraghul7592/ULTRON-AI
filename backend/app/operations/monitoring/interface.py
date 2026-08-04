from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from app.operations.domain.enums import ComponentType
    from app.operations.domain.models import ComponentHealth


class NotConfiguredError(Exception):
    """Raised by a monitor when its dependency is not configured."""


@runtime_checkable
class Monitor(Protocol):
    component_type: ComponentType
    component_name: str

    async def check(self) -> ComponentHealth: ...
