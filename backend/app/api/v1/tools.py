from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from app.api.v1.auth import verify_token
from app.core.logging import get_logger
from app.tools.router import ToolRouter

router = APIRouter(prefix="/tools", tags=["tools"], dependencies=[Depends(verify_token)])
logger = get_logger(__name__)


def _get_tool_router(request: Request) -> ToolRouter | None:
    if hasattr(request.app.state, "tool_router"):
        return request.app.state.tool_router
    return None


@router.get("")
async def list_tools(tool_router: ToolRouter | None = Depends(_get_tool_router)) -> list[dict]:
    if tool_router is None:
        return []
    tools = tool_router.get_all_tools()
    return [
        {
            "name": t.name,
            "description": t.description,
            "parameters": t.parameters,
        }
        for t in tools
    ]


@router.get("/definitions")
async def get_tool_definitions(tool_router: ToolRouter | None = Depends(_get_tool_router)) -> list[dict]:
    if tool_router is None:
        return []
    return tool_router.get_tool_definitions()


class ToolExecuteRequest(BaseModel):
    name: str
    arguments: dict = {}


@router.post("/execute")
async def execute_tool(
    request: ToolExecuteRequest,
    tool_router: ToolRouter | None = Depends(_get_tool_router),
) -> dict:
    if tool_router is None:
        return {"error": "Tool router not initialized"}
    try:
        result = await tool_router.execute_tool(request.name, **request.arguments)
        return {"result": result, "success": True}
    except Exception as e:
        return {"error": str(e), "success": False}


@router.get("/plugins")
async def list_plugins(tool_router: ToolRouter | None = Depends(_get_tool_router)) -> dict:
    if tool_router is None:
        return {"plugins": [], "total": 0}
    return tool_router.get_stats()