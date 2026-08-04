from __future__ import annotations

from typing import Any

import httpx

from app.plugins.base import PluginInterface, PluginStatus
from app.services.google_oauth import GoogleOAuthService
from app.tools.base import BaseTool


class GoogleDriveSearchTool(BaseTool):
    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None

    @property
    def name(self) -> str:
        return "search_google_drive"

    @property
    def description(self) -> str:
        return "Search files in Google Drive by name or content"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "max_results": {"type": "integer", "default": 10},
                "mime_type": {"type": "string", "description": "Filter by MIME type"},
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
            search_query = f"name contains '{query}' or fullText contains '{query}'"
            response = await self._client.get(
                "https://www.googleapis.com/drive/v3/files",
                headers={"Authorization": f"Bearer {token}"},
                params={
                    "q": search_query,
                    "maxResults": max_results,
                    "fields": "files(id,name,mimeType,size,modifiedTime,webViewLink)",
                },
            )
            response.raise_for_status()
            data = response.json()
            files = data.get("files", [])
            if not files:
                return f"No files found for '{query}'"
            results = [f"Found {len(files)} files:"]
            for f in files:
                size = f.get("size", "N/A")
                if size != "N/A":
                    size = f"{int(size) // 1024}KB"
                results.append(
                    f"- {f['name']} ({f['mimeType']}, {size}) "
                    f"Modified: {f.get('modifiedTime', 'N/A')}",
                )
            return "\n".join(results)
        except Exception:
            return "Drive search failed"

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()


class GoogleDriveReadTool(BaseTool):
    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None

    @property
    def name(self) -> str:
        return "read_google_drive_file"

    @property
    def description(self) -> str:
        return "Read content of a Google Drive file"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "file_id": {"type": "string", "description": "Google Drive file ID"},
            },
            "required": ["file_id"],
        }

    async def execute(self, **kwargs: Any) -> str:
        file_id = kwargs.get("file_id", "")
        user_id = kwargs.get("user_id", "")

        oauth = await GoogleOAuthService.for_user(user_id) if user_id else GoogleOAuthService()
        token = await oauth.get_access_token()
        if not token or not file_id:
            return "Google account not connected. Please authorize ULTRON first."

        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)

        try:
            meta_resp = await self._client.get(
                f"https://www.googleapis.com/drive/v3/files/{file_id}",
                headers={"Authorization": f"Bearer {token}"},
                params={"fields": "name,mimeType,size"},
            )
            meta_resp.raise_for_status()
            meta = meta_resp.json()
            mime = meta.get("mimeType", "")

            if "google-apps" in mime:
                export_mime = "text/plain"
                if "document" in mime:
                    export_mime = "text/plain"
                elif "spreadsheet" in mime:
                    export_mime = "text/csv"
                resp = await self._client.get(
                    f"https://www.googleapis.com/drive/v3/files/{file_id}/export",
                    headers={"Authorization": f"Bearer {token}"},
                    params={"mimeType": export_mime},
                )
            else:
                resp = await self._client.get(
                    f"https://www.googleapis.com/drive/v3/files/{file_id}",
                    headers={"Authorization": f"Bearer {token}"},
                    params={"alt": "media"},
                )
            resp.raise_for_status()
            content = resp.text
            return f"File: {meta.get('name', file_id)}\n\n{content[:10000]}"
        except Exception:
            return "File read failed"

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()


class Plugin(PluginInterface):
    @property
    def name(self) -> str:
        return "google_drive"

    @property
    def version(self) -> str:
        return "2.0.0"

    @property
    def description(self) -> str:
        return "Google Drive file search and reading"

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
                GoogleDriveSearchTool(),
                GoogleDriveReadTool(),
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
