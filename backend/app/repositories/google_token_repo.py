from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: TC002

from app.models.google_token import GoogleToken


class GoogleTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_user_id(self, user_id: str) -> GoogleToken | None:
        result = await self.session.execute(
            select(GoogleToken).where(GoogleToken.user_id == user_id),
        )
        return result.scalar_one_or_none()

    async def upsert(self, user_id: str, encrypted_refresh_token: str, scopes: str) -> GoogleToken:
        existing = await self.get_by_user_id(user_id)
        if existing:
            existing.encrypted_refresh_token = encrypted_refresh_token
            existing.scopes = scopes
            return existing
        token = GoogleToken(
            user_id=user_id,
            encrypted_refresh_token=encrypted_refresh_token,
            scopes=scopes,
        )
        self.session.add(token)
        await self.session.flush()
        return token

    async def delete_by_user_id(self, user_id: str) -> bool:
        token = await self.get_by_user_id(user_id)
        if token:
            await self.session.delete(token)
            await self.session.flush()
            return True
        return False
