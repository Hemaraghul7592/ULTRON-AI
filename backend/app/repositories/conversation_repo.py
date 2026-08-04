from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: TC002
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundException
from app.models.conversation import Conversation, Message
from app.schemas.conversation import ConversationCreate, MessageCreate  # noqa: TC001


class ConversationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, data: ConversationCreate, user_id: str) -> Conversation:
        conversation = Conversation(
            user_id=user_id,
            title=data.title,
            model=data.model,
            system_prompt=data.system_prompt,
        )
        self.session.add(conversation)
        await self.session.flush()
        return conversation

    async def get(self, conversation_id: str, user_id: str) -> Conversation | None:
        result = await self.session.execute(
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(Conversation.id == conversation_id, Conversation.user_id == user_id),
        )
        return result.scalar_one_or_none()

    async def list_all(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Conversation], int]:
        query = select(Conversation).where(Conversation.user_id == user_id)
        count_result = await self.session.execute(
            select(func.count()).select_from(query.subquery()),
        )
        total = count_result.scalar_one()

        offset = (page - 1) * page_size
        result = await self.session.execute(
            query.order_by(Conversation.updated_at.desc()).offset(offset).limit(page_size),
        )
        conversations = list(result.scalars().all())
        return conversations, total

    async def update(
        self,
        conversation_id: str,
        data: dict,
        user_id: str,
    ) -> Conversation | None:
        conversation = await self.get(conversation_id, user_id)
        if not conversation:
            return None
        for key, value in data.items():
            if value is not None:
                setattr(conversation, key, value)
        conversation.updated_at = datetime.now(UTC)
        await self.session.flush()
        return conversation

    async def delete(self, conversation_id: str, user_id: str) -> bool:
        conversation = await self.get(conversation_id, user_id)
        if not conversation:
            return False
        await self.session.delete(conversation)
        await self.session.flush()
        return True

    async def add_message(
        self,
        conversation_id: str,
        data: MessageCreate,
        user_id: str,
        model: str | None = None,
    ) -> Message:
        conversation = await self.get(conversation_id, user_id)
        if conversation is None:
            raise NotFoundException("Conversation", conversation_id)
        message = Message(
            conversation_id=conversation_id,
            role=data.role,
            content=data.content,
            model=model,
        )
        self.session.add(message)
        conversation.updated_at = datetime.now(UTC)
        await self.session.flush()
        return message

    async def get_messages(
        self,
        conversation_id: str,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Message]:
        result = await self.session.execute(
            select(Message)
            .join(Conversation, Conversation.id == Message.conversation_id)
            .where(
                Message.conversation_id == conversation_id,
                Conversation.user_id == user_id,
            )
            .order_by(Message.created_at.asc())
            .offset(offset)
            .limit(limit),
        )
        return list(result.scalars().all())

    async def get_message_counts(self, conversation_ids: list[str], user_id: str) -> dict[str, int]:
        if not conversation_ids:
            return {}
        result = await self.session.execute(
            select(Message.conversation_id, func.count(Message.id))
            .join(Conversation, Conversation.id == Message.conversation_id)
            .where(
                Message.conversation_id.in_(conversation_ids),
                Conversation.user_id == user_id,
            )
            .group_by(Message.conversation_id),
        )
        return {row[0]: row[1] for row in result.all()}

    async def get_recent_messages(
        self,
        conversation_id: str,
        user_id: str,
        limit: int = 20,
    ) -> list[Message]:
        subq = (
            select(Message)
            .join(Conversation, Conversation.id == Message.conversation_id)
            .where(
                Message.conversation_id == conversation_id,
                Conversation.user_id == user_id,
            )
            .order_by(Message.created_at.desc())
            .limit(limit)
        ).subquery()
        result = await self.session.execute(
            select(Message).select_from(subq).order_by(subq.c.created_at.asc()),
        )
        return list(result.scalars().all())
