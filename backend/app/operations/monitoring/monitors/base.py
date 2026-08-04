from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.operations.domain.enums import ComponentType, EnvironmentType, HealthStatus
from app.operations.domain.value_objects import utc_now
from app.operations.monitoring.interface import NotConfiguredError

if TYPE_CHECKING:
    from app.operations.domain.models import ComponentHealth


def _build_health(
    component_type: ComponentType,
    component_name: str,
    environment: EnvironmentType,
    status: HealthStatus,
    score: float,
    message: str,
    details: dict[str, Any] | None = None,
) -> ComponentHealth:
    from app.operations.domain.models import ComponentHealth

    return ComponentHealth(
        component_id=f"{component_type.value}:{component_name}",
        component_type=component_type,
        component_name=component_name,
        environment=environment,
        status=status,
        score=score,
        message=message,
        observed_at=utc_now(),
        details=details or {},
    )


def _healthy(
    component_type: ComponentType,
    component_name: str,
    environment: EnvironmentType,
    message: str = "Component is healthy",
    details: dict[str, Any] | None = None,
) -> ComponentHealth:
    return _build_health(
        component_type, component_name, environment, HealthStatus.HEALTHY, 100.0, message, details
    )


def _warning(
    component_type: ComponentType,
    component_name: str,
    environment: EnvironmentType,
    message: str,
    score: float,
    details: dict[str, Any] | None = None,
) -> ComponentHealth:
    return _build_health(
        component_type, component_name, environment, HealthStatus.WARNING, score, message, details
    )


def _critical(
    component_type: ComponentType,
    component_name: str,
    environment: EnvironmentType,
    message: str,
    score: float,
    details: dict[str, Any] | None = None,
) -> ComponentHealth:
    return _build_health(
        component_type, component_name, environment, HealthStatus.CRITICAL, score, message, details
    )


def _offline(
    component_type: ComponentType,
    component_name: str,
    environment: EnvironmentType,
    message: str = "Component is offline",
    details: dict[str, Any] | None = None,
) -> ComponentHealth:
    return _build_health(
        component_type, component_name, environment, HealthStatus.OFFLINE, 0.0, message, details
    )


def _not_configured(
    component_type: ComponentType,
    component_name: str,
    environment: EnvironmentType,
    message: str = "Component is not configured",
    details: dict[str, Any] | None = None,
) -> ComponentHealth:
    return _build_health(
        component_type,
        component_name,
        environment,
        HealthStatus.NOT_CONFIGURED,
        0.0,
        message,
        details,
    )


class BaseMonitor:
    component_type: ComponentType
    component_name: str

    def __init__(self, environment: EnvironmentType) -> None:
        self.environment = environment

    async def check(self) -> ComponentHealth:
        try:
            return await self._do_check()
        except NotConfiguredError as exc:
            return _not_configured(
                self.component_type,
                self.component_name,
                self.environment,
                message=str(exc),
            )
        except Exception as exc:  # noqa: BLE001
            return _offline(
                self.component_type,
                self.component_name,
                self.environment,
                message=f"Check failed: {exc}",
                details={"error": str(exc), "error_type": type(exc).__name__},
            )

    async def _do_check(self) -> ComponentHealth:
        raise NotImplementedError
