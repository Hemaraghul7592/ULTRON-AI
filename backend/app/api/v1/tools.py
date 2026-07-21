from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

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
async def list_tools(pm: PluginManager | None = Depends(_get_plugin_manager)) -> list[dict]:
    if pm is None:
        return []
    return pm.get_all_tools()


@router.get("/definitions")
async def get_tool_definitions(pm: PluginManager | None = Depends(_get_plugin_manager)) -> list[dict]:
    if pm is None:
        return []
    return pm.get_tool_definitions()


class ToolExecuteRequest(BaseModel):
    name: str
    arguments: dict = {}


@router.post("/execute")
async def execute_tool(
    request: ToolExecuteRequest,
    pm: PluginManager | None = Depends(_get_plugin_manager),
) -> dict:
    if pm is None:
        raise HTTPException(status_code=503, detail="Plugin manager not initialized")
    return await pm.execute_tool_safe(request.name, **request.arguments)


@router.get("/plugins")
async def list_plugins(pm: PluginManager | None = Depends(_get_plugin_manager)) -> dict:
    if pm is None:
        return {"plugins": [], "total": 0}
    return pm.get_stats()


@router.get("/health")
async def plugins_health(pm: PluginManager | None = Depends(_get_plugin_manager)) -> dict:
    if pm is None:
        return {"status": "not_initialized"}
    return await pm.health_check()


@router.get("/health/{plugin_name}")
async def plugin_health(
    plugin_name: str,
    pm: PluginManager | None = Depends(_get_plugin_manager),
) -> dict:
    if pm is None:
        raise HTTPException(status_code=503, detail="Plugin manager not initialized")
    health = await pm.health_check(plugin_name)
    if health.get("status") == "unavailable" and health.get("error") == "not_found":
        raise HTTPException(status_code=404, detail=f"Plugin '{plugin_name}' not found")
    return health


@router.get("/status")
async def plugin_statuses(pm: PluginManager | None = Depends(_get_plugin_manager)) -> dict:
    if pm is None:
        return {}
    return pm.get_all_statuses()