from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.database import get_session
from app.core.security import create_access_token, decode_access_token
from app.schemas.auth import TokenResponse, UserCreate, UserLogin
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer(auto_error=False)


async def verify_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    payload = decode_access_token(credentials.credentials)
    if "user_id" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing user_id",
        )
    return payload


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin) -> TokenResponse:
    session_factory = get_session()
    async with session_factory() as session:
        auth = AuthService(session)
        return await auth.login(data)


@router.post("/register", response_model=TokenResponse)
async def register(data: UserCreate) -> TokenResponse:
    session_factory = get_session()
    async with session_factory() as session:
        auth = AuthService(session)
        return await auth.register(data)


@router.get("/verify")
async def verify_auth(user: dict = Depends(verify_token)) -> dict:
    return {"authenticated": True, "user": user.get("sub", "unknown")}
