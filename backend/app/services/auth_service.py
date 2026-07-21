from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password, verify_password
from app.repositories.user_repo import UserRepository
from app.schemas.auth import TokenResponse, UserCreate, UserLogin


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repo = UserRepository(session)

    async def register(self, data: UserCreate) -> TokenResponse:
        existing = await self.user_repo.get_by_username(data.username)
        if existing:
            raise ValueError("Username already exists")
        hashed = hash_password(data.password)
        user = await self.user_repo.create(data, hashed)
        await self.session.commit()
        token = create_access_token({"sub": user.username, "user_id": user.id, "role": "admin"})
        return TokenResponse(access_token=token, expires_in=86400)

    async def login(self, data: UserLogin) -> TokenResponse:
        user = await self.user_repo.get_by_username(data.username)
        if not user or not verify_password(data.password, user.hashed_password):
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )
        token = create_access_token({"sub": user.username, "user_id": user.id, "role": "admin"})
        return TokenResponse(access_token=token, expires_in=86400)
