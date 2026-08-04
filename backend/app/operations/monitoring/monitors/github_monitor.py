from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.config import get_settings
from app.operations.domain.enums import ComponentType
from app.operations.monitoring.monitors.base import (
    BaseMonitor,
    _healthy,
    _not_configured,
    _offline,
)

if TYPE_CHECKING:
    from app.operations.domain.models import ComponentHealth


class GithubMonitor(BaseMonitor):
    component_type = ComponentType.GITHUB_ACTIONS
    component_name = "github-api"

    async def _do_check(self) -> ComponentHealth:
        settings = get_settings()
        token = settings.GITHUB_TOKEN
        if not token:
            return _not_configured(
                self.component_type,
                self.component_name,
                self.environment,
                message="GitHub token not configured",
            )

        try:
            import httpx

            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    "https://api.github.com/",
                    headers={"Authorization": f"token {token}"},
                )
                if resp.status_code == 200:
                    return _healthy(
                        self.component_type,
                        self.component_name,
                        self.environment,
                        message="GitHub API is accessible",
                    )
                return _offline(
                    self.component_type,
                    self.component_name,
                    self.environment,
                    message=f"GitHub API returned {resp.status_code}",
                    details={"status_code": str(resp.status_code)},
                )
        except Exception as exc:  # noqa: BLE001
            return _offline(
                self.component_type,
                self.component_name,
                self.environment,
                message=f"GitHub API check failed: {exc}",
                details={"error": str(exc)},
            )
