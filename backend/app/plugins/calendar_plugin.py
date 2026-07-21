from __future__ import annotations

from typing import Any

import httpx

from app.services.google_oauth import GoogleOAuthService
from app.plugins.base import PluginInterface, PluginStatus
from app.tools.base import BaseTool


class CalendarListTool(BaseTool):
    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None

    @property
    def name(self) -> str:
        return "list_calendar_events"

    @property
    def description(self) -> str:
        return "List upcoming Google Calendar events"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "days": {"type": "integer", "description": "Number of days ahead", "default": 7},
                "max_results": {"type": "integer", "default": 20},
                "calendar_id": {"type": "string", "default": "primary"},
            },
        }

    async def execute(self, **kwargs: Any) -> str:
        days = kwargs.get("days", 7)
        max_results = kwargs.get("max_results", 20)
        calendar_id = kwargs.get("calendar_id", "primary")
        user_id = kwargs.get("user_id", "")

        oauth = await GoogleOAuthService.for_user(user_id) if user_id else GoogleOAuthService()
        token = await oauth.get_access_token()
        if not token:
            return "Google account not connected. Please authorize ULTRON first."

        if self._client is None:
            self._client = httpx.AsyncClient(timeout=15.0)

        try:
            from datetime import datetime, timedelta, timezone
            now = datetime.now(timezone.utc)
            time_max = now + timedelta(days=days)

            resp = await self._client.get(
                f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events",
                headers={"Authorization": f"Bearer {token}"},
                params={
                    "timeMin": now.isoformat(),
                    "timeMax": time_max.isoformat(),
                    "maxResults": max_results,
                    "singleEvents": True,
                    "orderBy": "startTime",
                },
            )
            resp.raise_for_status()
            data = resp.json()
            events = data.get("items", [])
            if not events:
                return f"No events in the next {days} days"
            results = [f"Upcoming events ({len(events)}):"]
            for event in events:
                start = event.get("start", {}).get("dateTime", event.get("start", {}).get("date", ""))
                summary = event.get("summary", "No title")
                location = event.get("location", "")
                line = f"- {start}: {summary}"
                if location:
                    line += f" @ {location}"
                results.append(line)
            return "\n".join(results)
        except Exception as e:
            return f"Calendar error: {e}"

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()


class CalendarCreateTool(BaseTool):
    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None

    @property
    def name(self) -> str:
        return "create_calendar_event"

    @property
    def description(self) -> str:
        return "Create a Google Calendar event"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "summary": {"type": "string", "description": "Event title"},
                "start_datetime": {"type": "string", "description": "Start (ISO 8601)"},
                "end_datetime": {"type": "string", "description": "End (ISO 8601)"},
                "description": {"type": "string", "description": "Event description"},
                "location": {"type": "string", "description": "Event location"},
            },
            "required": ["summary", "start_datetime", "end_datetime"],
        }

    async def execute(self, **kwargs: Any) -> str:
        summary = kwargs.get("summary", "")
        start = kwargs.get("start_datetime", "")
        end = kwargs.get("end_datetime", "")
        description = kwargs.get("description", "")
        location = kwargs.get("location", "")
        user_id = kwargs.get("user_id", "")

        oauth = await GoogleOAuthService.for_user(user_id) if user_id else GoogleOAuthService()
        token = await oauth.get_access_token()
        if not token:
            return "Google account not connected. Please authorize ULTRON first."

        if self._client is None:
            self._client = httpx.AsyncClient(timeout=15.0)

        try:
            event = {
                "summary": summary,
                "start": {"dateTime": start, "timeZone": "UTC"},
                "end": {"dateTime": end, "timeZone": "UTC"},
            }
            if description:
                event["description"] = description
            if location:
                event["location"] = location

            resp = await self._client.post(
                "https://www.googleapis.com/calendar/v3/calendars/primary/events",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json=event,
            )
            resp.raise_for_status()
            data = resp.json()
            return f"Created event: {data.get('summary', summary)} at {data.get('htmlLink', '')}"
        except Exception as e:
            return f"Calendar create error: {e}"

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()


class Plugin(PluginInterface):
    @property
    def name(self) -> str:
        return "calendar"

    @property
    def version(self) -> str:
        return "2.0.0"

    @property
    def description(self) -> str:
        return "Google Calendar event management"

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
                CalendarListTool(),
                CalendarCreateTool(),
            ]

    async def health_check(self) -> dict:
        import time
        if not self._has_oauth:
            return {"status": PluginStatus.AUTH_FAILED, "message": "Google OAuth not configured", "last_check": time.time()}
        if not self._tools:
            return {"status": PluginStatus.DISABLED, "message": "No tools initialized", "last_check": time.time()}
        return {"status": PluginStatus.AVAILABLE, "message": "Google credentials configured", "last_check": time.time()}

    async def validate(self) -> bool:
        return self._has_oauth

    async def cleanup(self) -> None:
        for tool in self._tools:
            if hasattr(tool, "close"):
                await tool.close()