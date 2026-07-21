from __future__ import annotations

import json
import time
import uuid
from typing import Any, AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.context_builder import ContextBuilder
from app.ai.prompt_builder import PromptBuilder
from app.ai.service import AIService
from app.ai.tool_executor import ToolExecutor
from app.core.config import get_settings
from app.core.logging import get_logger
from app.memory.service import MemoryService
from app.repositories.conversation_repo import ConversationRepository
from app.repositories.token_repo import TokenRepository
from app.schemas.ai import ChatRequest, ChatResponse, StreamChunk, ToolCall, ToolResult
from app.schemas.conversation import ConversationCreate, MessageCreate

logger = get_logger(__name__)


class ChatService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.ai_service = AIService()
        self.prompt_builder = PromptBuilder()
        self.context_builder = ContextBuilder()
        self.tool_executor = ToolExecutor()
        self.conversation_repo = ConversationRepository(session)
        self.token_repo = TokenRepository(session)
        self.memory_service = MemoryService(session)

    def set_tool_executor(self, executor: ToolExecutor) -> None:
        self.tool_executor = executor

    async def chat(self, request: ChatRequest, user_id: str) -> ChatResponse:
        start = time.monotonic()
        settings = get_settings()

        conversation_id = request.conversation_id
        if not conversation_id:
            conv = await self.conversation_repo.create(ConversationCreate(title=None), user_id=user_id)
            conversation_id = conv.id

        history = []
        if request.conversation_id:
            messages = await self.conversation_repo.get_recent_messages(conversation_id, user_id, limit=20)
            history = [{"role": m.role, "content": m.content} for m in messages]

        memory_context = ""
        if request.use_memory:
            memory_context = await self.memory_service.get_context_for_query(request.message, user_id=user_id)

        tools = None
        if request.use_tools and self.tool_executor.has_tools():
            tools = self.tool_executor.get_tool_definitions()

        messages = self.prompt_builder.build_messages(
            user_message=request.message,
            conversation_history=history,
            system_prompt=request.system_prompt,
            memory_context=memory_context,
        )

        messages = self.context_builder.truncate_to_fit(messages)

        provider = request.provider or settings.DEFAULT_AI_PROVIDER
        result = await self.ai_service.chat(
            messages=messages,
            provider=provider,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            tools=tools,
        )

        tool_calls = []
        tool_results = []
        max_tool_rounds = 5
        round_count = 0

        while result.get("tool_calls") and round_count < max_tool_rounds:
            round_count += 1
            for tc in result["tool_calls"]:
                tool_calls.append(ToolCall(
                    id=tc["id"],
                    name=tc["name"],
                    arguments=tc["arguments"],
                ))
                exec_result = await self.tool_executor.execute(tc)
                tool_results.append(ToolResult(
                    tool_call_id=exec_result["tool_call_id"],
                    name=exec_result["name"],
                    result=exec_result["result"],
                    success=exec_result["success"],
                    error=exec_result.get("error"),
                ))

            messages.append({
                "role": "assistant",
                "content": result.get("content", ""),
                "tool_calls": result["tool_calls"],
            })
            for tr in tool_results:
                messages.append({
                    "role": "tool",
                    "content": tr.result,
                    "tool_call_id": tr.tool_call_id,
                })

            result = await self.ai_service.chat(
                messages=messages,
                provider=provider,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                tools=tools,
            )

        response_text = result.get("content", "")
        tokens_used = result.get("tokens_used", 0)
        prompt_tokens = result.get("prompt_tokens", 0)
        completion_tokens = result.get("completion_tokens", 0)

        await self.conversation_repo.add_message(
            conversation_id,
            MessageCreate(content=request.message, role="user"),
            user_id=user_id,
        )
        msg = await self.conversation_repo.add_message(
            conversation_id,
            MessageCreate(content=response_text, role="assistant"),
            user_id=user_id,
            model=result.get("model"),
        )

        await self.token_repo.record(
            provider=provider,
            model=result.get("model", settings.GROQ_MODEL),
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            conversation_id=conversation_id,
            user_id=user_id,
        )

        latency_ms = (time.monotonic() - start) * 1000

        return ChatResponse(
            message=response_text,
            conversation_id=conversation_id,
            message_id=msg.id,
            model=result.get("model", ""),
            provider=provider,
            tokens_used=tokens_used,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            tool_calls=tool_calls,
            tool_results=tool_results,
            latency_ms=latency_ms,
            finish_reason=result.get("finish_reason", "stop"),
        )

    async def chat_stream(
        self, request: ChatRequest, user_id: str
    ) -> AsyncIterator[StreamChunk]:
        settings = get_settings()
        conversation_id = request.conversation_id
        if not conversation_id:
            conv = await self.conversation_repo.create(ConversationCreate(title=None), user_id=user_id)
            conversation_id = conv.id

        history = []
        if request.conversation_id:
            messages = await self.conversation_repo.get_recent_messages(conversation_id, user_id, limit=20)
            history = [{"role": m.role, "content": m.content} for m in messages]

        memory_context = ""
        if request.use_memory:
            memory_context = await self.memory_service.get_context_for_query(request.message, user_id=user_id)

        messages = self.prompt_builder.build_messages(
            user_message=request.message,
            conversation_history=history,
            system_prompt=request.system_prompt,
            memory_context=memory_context,
        )
        messages = self.context_builder.truncate_to_fit(messages)

        provider = request.provider or settings.DEFAULT_AI_PROVIDER
        full_content = ""

        try:
            async for chunk in self.ai_service.chat_stream(
                messages=messages,
                provider=provider,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            ):
                content = chunk.get("content", "")
                full_content += content
                done = chunk.get("done", False)
                yield StreamChunk(
                    content=content,
                    done=done,
                    finish_reason=chunk.get("finish_reason"),
                )
        except Exception as e:
            logger.error("stream_error", error=str(e))
            yield StreamChunk(content="", done=True, finish_reason="error")
            return

        if full_content:
            await self.conversation_repo.add_message(
                conversation_id,
                MessageCreate(content=request.message, role="user"),
                user_id=user_id,
            )
            await self.conversation_repo.add_message(
                conversation_id,
                MessageCreate(content=full_content, role="assistant"),
                user_id=user_id,
            )

    async def close(self) -> None:
        await self.ai_service.close()