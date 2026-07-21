from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel

from app.api.v1.auth import verify_token
from app.core.config import get_settings
from app.core.database import get_session
from app.core.encryption import encrypt_value
from app.core.exceptions import AuthenticationException
from app.core.logging import get_logger
from app.core.security import create_access_token, decode_access_token
from app.repositories.google_token_repo import GoogleTokenRepository
from app.services.google_oauth import GoogleOAuthService

router = APIRouter(prefix="/google/auth", tags=["google_auth"])
logger = get_logger(__name__)


class StatusResponse(BaseModel):
    connected: bool
    scopes: list[str] | None = None
    email: str | None = None


class DisconnectResponse(BaseModel):
    disconnected: bool
    message: str


@router.get("/login")
async def google_auth_login(
    request: Request,
    user: dict = Depends(verify_token),
) -> dict:
    settings = get_settings()
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth is not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env",
        )

    session_factory = get_session()
    async with session_factory() as session:
        repo = GoogleTokenRepository(session)
        existing = await repo.get_by_user_id(user["user_id"])
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Google account already connected. Disconnect first to reconnect.",
            )

    state = create_access_token(
        data={"sub": user["user_id"], "purpose": "oauth_state"},
        expires_delta=timedelta(minutes=10),
    )

    redirect_uri = str(request.base_url).rstrip("/") + "/api/v1/google/auth/callback"
    oauth = GoogleOAuthService()
    url = oauth.get_authorization_url(state=state, redirect_uri=redirect_uri)
    return {"authorization_url": url}


@router.get("/callback")
async def google_auth_callback(
    request: Request,
    code: str | None = Query(None),
    state: str | None = Query(None),
    error: str | None = Query(None),
) -> dict:
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Google OAuth error: {error}",
        )

    if not code or not state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing authorization code or state parameter",
        )

    try:
        payload = decode_access_token(state)
    except AuthenticationException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired state parameter. Please start again from /api/v1/google/auth/login",
        )

    if payload.get("purpose") != "oauth_state":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state parameter.",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state parameter.",
        )

    redirect_uri = str(request.base_url).rstrip("/") + "/api/v1/google/auth/callback"
    oauth = GoogleOAuthService()
    token_data = await oauth.exchange_code(code, redirect_uri)

    refresh_token = token_data.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google did not return a refresh token. Ensure you have granted offline access.",
        )

    encrypted = encrypt_value(refresh_token)
    scopes_str = " ".join(token_data.get("scope", "").split(","))

    session_factory = get_session()
    async with session_factory() as session:
        repo = GoogleTokenRepository(session)
        await repo.upsert(user_id, encrypted, scopes_str)
        await session.commit()

    logger.info("google_oauth_connected", user_id=user_id)

    return {
        "status": "success",
        "message": "Google account connected successfully",
    }


@router.get("/status", response_model=StatusResponse)
async def google_auth_status(
    request: Request,
    user: dict = Depends(verify_token),
) -> StatusResponse:
    session_factory = get_session()
    async with session_factory() as session:
        repo = GoogleTokenRepository(session)
        token = await repo.get_by_user_id(user["user_id"])

    if not token:
        return StatusResponse(connected=False)

    scopes = token.scopes.split() if token.scopes else []
    return StatusResponse(connected=True, scopes=scopes if scopes else None)


@router.post("/disconnect", response_model=DisconnectResponse)
async def google_auth_disconnect(
    request: Request,
    user: dict = Depends(verify_token),
) -> DisconnectResponse:
    session_factory = get_session()
    async with session_factory() as session:
        repo = GoogleTokenRepository(session)
        deleted = await repo.delete_by_user_id(user["user_id"])

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Google account connection found",
        )

    logger.info("google_oauth_disconnected", user_id=user["user_id"])
    return DisconnectResponse(disconnected=True, message="Google account disconnected")
