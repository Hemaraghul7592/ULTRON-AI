from __future__ import annotations

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import verify_token
from app.core.database import get_session
from app.repositories.conversation_repo import ConversationRepository
from app.schemas.conversation import (
    ConversationCreate,
    ConversationDetailResponse,
    ConversationListResponse,
    ConversationResponse,
    ConversationUpdate,
    MessageCreate,
    MessageResponse,
)

router = APIRouter(
    prefix="/conversations", tags=["conversations"], dependencies=[Depends(verify_token)],
)


async def get_repo() -> AsyncSession:
    session_factory = get_session()
    async with session_factory() as session:
        yield session


@router.get("", response_model=ConversationListResponse)
async def list_conversations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: dict = Depends(verify_token),
) -> ConversationListResponse:
    user_id = user["user_id"]
    session_factory = get_session()
    async with session_factory() as session:
        repo = ConversationRepository(session)
        conversations, total = await repo.list_all(user_id=user_id, page=page, page_size=page_size)
        conv_ids = [c.id for c in conversations]
        message_counts = await repo.get_message_counts(conv_ids, user_id=user_id)
        return ConversationListResponse(
            conversations=[
                ConversationResponse(
                    id=c.id,
                    title=c.title,
                    model=c.model,
                    system_prompt=c.system_prompt,
                    created_at=c.created_at,
                    updated_at=c.updated_at,
                    message_count=message_counts.get(c.id, 0),
                )
                for c in conversations
            ],
            total=total,
            page=page,
            page_size=page_size,
        )


@router.post("", response_model=ConversationResponse, status_code=201)
async def create_conversation(
    data: ConversationCreate, user: dict = Depends(verify_token),
) -> ConversationResponse:
    user_id = user["user_id"]
    session_factory = get_session()
    async with session_factory() as session:
        repo = ConversationRepository(session)
        conv = await repo.create(data, user_id=user_id)
        await session.commit()
        return ConversationResponse(
            id=conv.id,
            title=conv.title,
            model=conv.model,
            system_prompt=conv.system_prompt,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
        )


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: str = Path(..., min_length=1, max_length=36),
    user: dict = Depends(verify_token),
) -> ConversationDetailResponse:
    user_id = user["user_id"]
    session_factory = get_session()
    async with session_factory() as session:
        repo = ConversationRepository(session)
        conv = await repo.get(conversation_id, user_id)
        if not conv:
            from app.core.exceptions import NotFoundExceptionHTTP

            raise NotFoundExceptionHTTP("Conversation", conversation_id)
        return ConversationDetailResponse(
            id=conv.id,
            title=conv.title,
            model=conv.model,
            system_prompt=conv.system_prompt,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            message_count=len(conv.messages) if conv.messages else 0,
            messages=[
                MessageResponse(
                    id=m.id,
                    role=m.role,
                    content=m.content,
                    model=m.model,
                    tokens_used=m.tokens_used,
                    tool_calls=m.tool_calls,
                    metadata_json=m.metadata_json,
                    created_at=m.created_at,
                )
                for m in conv.messages
            ],
        )


@router.patch("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    data: ConversationUpdate,
    conversation_id: str = Path(..., min_length=1, max_length=36),
    user: dict = Depends(verify_token),
) -> ConversationResponse:
    user_id = user["user_id"]
    session_factory = get_session()
    async with session_factory() as session:
        repo = ConversationRepository(session)
        conv = await repo.update(
            conversation_id, data.model_dump(exclude_unset=True), user_id=user_id,
        )
        if not conv:
            from app.core.exceptions import NotFoundExceptionHTTP

            raise NotFoundExceptionHTTP("Conversation", conversation_id)
        await session.commit()
        return ConversationResponse(
            id=conv.id,
            title=conv.title,
            model=conv.model,
            system_prompt=conv.system_prompt,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
        )


@router.delete("/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: str = Path(..., min_length=1, max_length=36),
    user: dict = Depends(verify_token),
) -> None:
    user_id = user["user_id"]
    session_factory = get_session()
    async with session_factory() as session:
        repo = ConversationRepository(session)
        deleted = await repo.delete(conversation_id, user_id=user_id)
        if not deleted:
            from app.core.exceptions import NotFoundExceptionHTTP

            raise NotFoundExceptionHTTP("Conversation", conversation_id)
        await session.commit()


@router.post("/{conversation_id}/messages", response_model=MessageResponse, status_code=201)
async def add_message(
    data: MessageCreate,
    conversation_id: str = Path(..., min_length=1, max_length=36),
    user: dict = Depends(verify_token),
) -> MessageResponse:
    user_id = user["user_id"]
    session_factory = get_session()
    async with session_factory() as session:
        repo = ConversationRepository(session)
        conv = await repo.get(conversation_id, user_id)
        if not conv:
            from app.core.exceptions import NotFoundExceptionHTTP

            raise NotFoundExceptionHTTP("Conversation", conversation_id)
        msg = await repo.add_message(conversation_id, data, user_id)
        await session.commit()
        return MessageResponse(
            id=msg.id,
            role=msg.role,
            content=msg.content,
            model=msg.model,
            tokens_used=msg.tokens_used,
            tool_calls=msg.tool_calls,
            metadata_json=msg.metadata_json,
            created_at=msg.created_at,
        )
