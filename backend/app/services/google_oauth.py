from __future__ import annotations

import time
from typing import Any

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
SCOPES_BY_SERVICE: dict[str, list[str]] = {
    "drive": ["https://www.googleapis.com/auth/drive.readonly"],
    "gmail": [
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.modify",
    ],
    "calendar": ["https://www.googleapis.com/auth/calendar"],
    "people": ["https://www.googleapis.com/auth/contacts.readonly"],
}

ALL_SCOPES = sorted(
    {
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
        *[s for scopes in SCOPES_BY_SERVICE.values() for s in scopes],
    }
)


class GoogleOAuthService:
    def __init__(self, encrypted_refresh_token: str | None = None) -> None:
        settings = get_settings()
        self._client_id = settings.GOOGLE_CLIENT_ID
        self._client_secret = settings.GOOGLE_CLIENT_SECRET
        self._encrypted_refresh_token = encrypted_refresh_token or ""
        self._access_token: str | None = None
        self._token_expiry: float = 0.0
        self._client: httpx.AsyncClient | None = None

    @classmethod
    async def for_user(cls, user_id: str) -> GoogleOAuthService:
        from app.core.database import get_session
        from app.repositories.google_token_repo import GoogleTokenRepository

        session_factory = get_session()
        async with session_factory() as session:
            repo = GoogleTokenRepository(session)
            token = await repo.get_by_user_id(user_id)
            encrypted = token.encrypted_refresh_token if token else ""
            return cls(encrypted_refresh_token=encrypted)

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=15.0)
        return self._client

    def is_configured(self) -> bool:
        settings = get_settings()
        return bool(settings.GOOGLE_CLIENT_ID) and bool(settings.GOOGLE_CLIENT_SECRET)

    def has_refresh_token(self) -> bool:
        return bool(self._encrypted_refresh_token)

    def get_authorization_url(self, state: str, redirect_uri: str) -> str:
        scopes = "+".join(ALL_SCOPES)
        return (
            f"{AUTH_URL}?"
            f"client_id={self._client_id}&"
            f"redirect_uri={redirect_uri}&"
            f"response_type=code&"
            f"scope={scopes}&"
            f"state={state}&"
            f"access_type=offline&"
            f"prompt=consent"
        )

    async def exchange_code(self, code: str, redirect_uri: str) -> dict[str, Any]:
        try:
            response = await self.client.post(
                TOKEN_URL,
                data={
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                },
            )
            response.raise_for_status()
            data = response.json()
            self._access_token = data.get("access_token")
            expires_in = data.get("expires_in", 3600)
            self._token_expiry = time.monotonic() + expires_in - 60
            return data
        except Exception as e:
            logger.error("google_oauth_exchange_failed", error=str(e))
            raise

    async def get_access_token(self) -> str | None:
        if not self.is_configured():
            return None
        if self._access_token and time.monotonic() < self._token_expiry:
            return self._access_token
        if not self._encrypted_refresh_token:
            return None
        await self._refresh_access_token()
        return self._access_token

    async def _refresh_access_token(self) -> None:
        try:
            from app.core.encryption import decrypt_value

            refresh_token = decrypt_value(self._encrypted_refresh_token)
            response = await self.client.post(
                TOKEN_URL,
                data={
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                },
            )
            response.raise_for_status()
            data = response.json()
            self._access_token = data.get("access_token")
            expires_in = data.get("expires_in", 3600)
            self._token_expiry = time.monotonic() + expires_in - 60
            logger.info("google_oauth_token_refreshed")
        except Exception as e:
            logger.error("google_oauth_refresh_failed", error=str(e))
            self._access_token = None
            self._token_expiry = 0.0

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
