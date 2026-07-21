from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from app.api.v1.auth import verify_token
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_session
from app.memory.engine import MemoryEngine
from app.schemas.ai import ChatRequest, ChatResponse
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"], dependencies=[Depends(verify_token)])


async def _get_chat_service(user_id: str) -> ChatService:
    session_factory = get_session()
    session = session_factory()
    await session.__aenter__()
    chat_service = ChatService(session)
    memory_engine = MemoryEngine(session)
    await memory_engine.initialize()
    chat_service.set_memory_engine(memory_engine)
    return chat_service


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest, user: dict = Depends(verify_token)) -> ChatResponse:
    user_id = user["user_id"]
    settings = get_settings()
    session_factory = get_session()
    async with session_factory() as session:
        chat_service = ChatService(session)
        memory_engine = MemoryEngine(session)
        await memory_engine.initialize()
        chat_service.set_memory_engine(memory_engine)

        result = await chat_service.chat(request, user_id=user_id)
        await session.commit()
        return result


@router.post("/stream")
async def chat_stream(request: ChatRequest, user: dict = Depends(verify_token)) -> StreamingResponse:
    user_id = user["user_id"]
    session_factory = get_session()

    async def event_generator():
        async with session_factory() as session:
            chat_service = ChatService(session)
            memory_engine = MemoryEngine(session)
            await memory_engine.initialize()
            chat_service.set_memory_engine(memory_engine)

            async for chunk in chat_service.chat_stream(request, user_id=user_id):
                data = json.dumps({
                    "content": chunk.content,
                    "done": chunk.done,
                    "finish_reason": chunk.finish_reason,
                })
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