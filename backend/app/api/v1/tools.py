from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.api.v1.auth import verify_token
from app.core.logging import get_logger
from app.plugins.manager import PluginManager

router = APIRouter(prefix="/tools", tags=["tools"], dependencies=[Depends(verify_token)])
logger = get_logger(__name__)


def _get_plugin_manager(request: Request) -> PluginManager | None:
    if hasattr(request.app.state, "plugin_manager"):
        return request.app.state.plugin_manager
    return None


@router.get("")
async def list_tools(pm: PluginManager | None = Depends(_get_plugin_manager)) -> list[dict]:  # noqa: B008 FastAPI Depends() convention
    if pm is None:
        return []
    return pm.get_all_tools()


@router.get("/definitions")
async def get_tool_definitions(
    pm: PluginManager | None = Depends(_get_plugin_manager),  # noqa: B008 FastAPI Depends() convention
) -> list[dict]:
    if pm is None:
        return []
    return pm.get_tool_definitions()


class ToolExecuteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    arguments: dict = Field(default_factory=dict)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not value or len(value) > 200:
            raise ValueError("Tool name must be between 1 and 200 characters")
        return value

    @field_validator("arguments")
    @classmethod
    def reject_caller_identity(cls, value: dict) -> dict:
        forbidden = {"user_id", "userId", "user", "owner_id", "ownerId"}
        if forbidden.intersection(value):
            raise ValueError("Caller identity must come from authentication")
        return value


@router.post("/execute")
async def execute_tool(
    request: ToolExecuteRequest,
    pm: PluginManager | None = Depends(_get_plugin_manager),  # noqa: B008 FastAPI Depends() convention
    user: dict = Depends(verify_token),  # noqa: B008 FastAPI Depends() convention
) -> dict:
    if pm is None:
        raise HTTPException(status_code=503, detail="Plugin manager not initialized")
    return await pm.execute_tool_safe(
        request.name,
        user_id=str(user["user_id"]),
        **request.arguments,
    )


@router.get("/plugins")
async def list_plugins(pm: PluginManager | None = Depends(_get_plugin_manager)) -> dict:  # noqa: B008 FastAPI Depends() convention
    if pm is None:
        return {"plugins": [], "total": 0}
    return pm.get_stats()


@router.get("/health")
async def plugins_health(pm: PluginManager | None = Depends(_get_plugin_manager)) -> dict:  # noqa: B008 FastAPI Depends() convention
    if pm is None:
        return {"status": "not_initialized"}
    return await pm.health_check()


@router.get("/health/{plugin_name}")
async def plugin_health(
    plugin_name: str,
    pm: PluginManager | None = Depends(_get_plugin_manager),  # noqa: B008 FastAPI Depends() convention
) -> dict:
    if pm is None:
        raise HTTPException(status_code=503, detail="Plugin manager not initialized")
    health = await pm.health_check(plugin_name)
    if health.get("status") == "unavailable" and health.get("error") == "not_found":
        raise HTTPException(status_code=404, detail=f"Plugin '{plugin_name}' not found")
    return health


@router.get("/status")
async def plugin_statuses(pm: PluginManager | None = Depends(_get_plugin_manager)) -> dict:  # noqa: B008 FastAPI Depends() convention
    if pm is None:
        return {}
    return pm.get_all_statuses()
