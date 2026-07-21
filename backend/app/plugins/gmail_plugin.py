from __future__ import annotations

from typing import Any

import httpx

from app.plugins.base import PluginInterface, PluginStatus
from app.services.google_oauth import GoogleOAuthService
from app.tools.base import BaseTool


class GmailSearchTool(BaseTool):
    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None

    @property
    def name(self) -> str:
        return "search_gmail"

    @property
    def description(self) -> str:
        return "Search Gmail emails"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Gmail search query"},
                "max_results": {"type": "integer", "default": 10},
            },
            "required": ["query"],
        }

    async def execute(self, **kwargs: Any) -> str:
        query = kwargs.get("query", "")
        max_results = kwargs.get("max_results", 10)
        user_id = kwargs.get("user_id", "")

        oauth = await GoogleOAuthService.for_user(user_id) if user_id else GoogleOAuthService()
        token = await oauth.get_access_token()
        if not token:
            return "Google account not connected. Please authorize ULTRON first."

        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)

        try:
            resp = await self._client.get(
                "https://gmail.googleapis.com/gmail/v1/users/me/messages",
                headers={"Authorization": f"Bearer {token}"},
                params={"q": query, "maxResults": max_results},
            )
            resp.raise_for_status()
            data = resp.json()
            messages = data.get("messages", [])
            if not messages:
                return f"No emails found for '{query}'"

            results = [f"Found {len(messages)} emails:"]
            for msg_data in messages[:10]:
                msg_resp = await self._client.get(
                    f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_data['id']}",
                    headers={"Authorization": f"Bearer {token}"},
                    params={"format": "metadata", "metadataHeaders": "Subject,From,Date"},
                )
                if msg_resp.status_code == 200:
                    msg = msg_resp.json()
                    headers = {
                        h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])
                    }
                    subject = headers.get("Subject", "No subject")
                    sender = headers.get("From", "Unknown")
                    results.append(f"- {subject} from {sender}")
            return "\n".join(results)
        except Exception as e:
            return f"Gmail search error: {e}"

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()


class GmailReadTool(BaseTool):
    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None

    @property
    def name(self) -> str:
        return "read_gmail_message"

    @property
    def description(self) -> str:
        return "Read a specific Gmail message"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "message_id": {"type": "string", "description": "Gmail message ID"},
            },
            "required": ["message_id"],
        }

    async def execute(self, **kwargs: Any) -> str:
        message_id = kwargs.get("message_id", "")
        user_id = kwargs.get("user_id", "")

        oauth = await GoogleOAuthService.for_user(user_id) if user_id else GoogleOAuthService()
        token = await oauth.get_access_token()
        if not token or not message_id:
            return "Google account not connected. Please authorize ULTRON first."

        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)

        try:
            resp = await self._client.get(
                f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{message_id}",
                headers={"Authorization": f"Bearer {token}"},
                params={"format": "full"},
            )
            resp.raise_for_status()
            msg = resp.json()
            headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
            subject = headers.get("Subject", "No subject")
            sender = headers.get("From", "Unknown")
            date = headers.get("Date", "Unknown")

            body = self._extract_body(msg.get("payload", {}))
            return f"From: {sender}\nDate: {date}\nSubject: {subject}\n\n{body[:5000]}"
        except Exception as e:
            return f"Gmail read error: {e}"

    def _extract_body(self, payload: dict) -> str:
        if "body" in payload and payload["body"].get("data"):
            import base64

            return base64.urlsafe_b64decode(payload["body"]["data"]).decode(
                "utf-8", errors="replace"
            )
        parts = payload.get("parts", [])
        for part in parts:
            if part.get("mimeType") == "text/plain":
                data = part.get("body", {}).get("data")
                if data:
                    import base64

                    return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
        return ""

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()


class Plugin(PluginInterface):
    @property
    def name(self) -> str:
        return "gmail"

    @property
    def version(self) -> str:
        return "2.0.0"

    @property
    def description(self) -> str:
        return "Gmail email management"

    @property
    def required_credentials(self) -> list[str]:
        return ["GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET"]

    def __init__(self) -> None:
        self._tools: list[BaseTool] = []
        self._has_oauth = False

    def get_tools(self) -> list[BaseTool]:
        return self._tools

    async def initialize(self, config: dict | None = None) -> None:
        from app.core.config import get_settings

        settings = get_settings()
        self._has_oauth = bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET)
        if self._has_oauth:
            self._tools = [
                GmailSearchTool(),
                GmailReadTool(),
            ]

    async def health_check(self) -> dict:
        import time

        if not self._has_oauth:
            return {
                "status": PluginStatus.AUTH_FAILED,
                "message": "Google OAuth not configured",
                "last_check": time.time(),
            }
        if not self._tools:
            return {
                "status": PluginStatus.DISABLED,
                "message": "No tools initialized",
                "last_check": time.time(),
            }
        return {
            "status": PluginStatus.AVAILABLE,
            "message": "Google credentials configured",
            "last_check": time.time(),
        }

    async def validate(self) -> bool:
        return self._has_oauth

    async def cleanup(self) -> None:
        for tool in self._tools:
            if hasattr(tool, "close"):
                await tool.close()
