from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from app.api.v1.auth import verify_token
from app.core.database import get_session
from app.plugins.manager import PluginManager
from app.schemas.ai import ChatRequest, ChatResponse
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"], dependencies=[Depends(verify_token)])


def _get_pm_from_request(http_request: Request) -> PluginManager | None:
    if hasattr(http_request.app.state, "plugin_manager"):
        return http_request.app.state.plugin_manager
    return None


@router.post("", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    http_request: Request,
    user: dict = Depends(verify_token),
) -> ChatResponse:
    user_id = user["user_id"]
    session_factory = get_session()
    async with session_factory() as session:
        pm = _get_pm_from_request(http_request)
        chat_service = ChatService(session, plugin_manager=pm)

        result = await chat_service.chat(body, user_id=user_id)
        await session.commit()
        return result


@router.post("/stream")
async def chat_stream(
    body: ChatRequest,
    http_request: Request,
    user: dict = Depends(verify_token),
) -> StreamingResponse:
    user_id = user["user_id"]
    session_factory = get_session()

    async def event_generator():
        async with session_factory() as session:
            pm = _get_pm_from_request(http_request)
            chat_service = ChatService(session, plugin_manager=pm)

            async for chunk in chat_service.chat_stream(body, user_id=user_id):
                data = json.dumps(
                    {
                        "content": chunk.content,
                        "done": chunk.done,
                        "finish_reason": chunk.finish_reason,
                    }
                )
                yield f"data: {data}\n\n"
            await session.commit()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
