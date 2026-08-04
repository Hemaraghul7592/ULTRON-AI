from __future__ import annotations

from typing import Any

import httpx

from app.services.google_oauth import GoogleOAuthService
from app.tools.base import BasePlugin, BaseTool


class PeopleSearchTool(BaseTool):
    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None

    @property
    def name(self) -> str:
        return "search_contacts"

    @property
    def description(self) -> str:
        return "Search Google Contacts using Google People API"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query for contacts"},
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
            self._client = httpx.AsyncClient(timeout=15.0)

        try:
            resp = await self._client.get(
                "https://people.googleapis.com/v1/people:searchContacts",
                headers={"Authorization": f"Bearer {token}"},
                params={
                    "query": query,
                    "pageSize": max_results,
                    "readMask": "names,emailAddresses,phoneNumbers,organizations",
                },
            )
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results", [])
            if not results:
                return f"No contacts found for '{query}'"
            output = [f"Contacts matching '{query}' ({len(results)}):"]
            for r in results:
                person = r.get("person", {})
                names = person.get("names", [])
                name = names[0].get("displayName", "Unknown") if names else "Unknown"
                emails = person.get("emailAddresses", [])
                email = emails[0].get("value", "") if emails else ""
                phones = person.get("phoneNumbers", [])
                phone = phones[0].get("value", "") if phones else ""
                orgs = person.get("organizations", [])
                org = orgs[0].get("name", "") if orgs else ""
                line = f"- {name}"
                if email:
                    line += f" ({email})"
                if phone:
                    line += f" {phone}"
                if org:
                    line += f" @ {org}"
                output.append(line)
            return "\n".join(output)
        except Exception:
            return "Contacts search failed"

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()


class PeopleProfileTool(BaseTool):
    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None

    @property
    def name(self) -> str:
        return "get_my_profile"

    @property
    def description(self) -> str:
        return "Get the authenticated user's Google profile information"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {},
        }

    async def execute(self, **kwargs: Any) -> str:
        user_id = kwargs.get("user_id", "")

        oauth = await GoogleOAuthService.for_user(user_id) if user_id else GoogleOAuthService()
        token = await oauth.get_access_token()
        if not token:
            return "Google account not connected. Please authorize ULTRON first."

        if self._client is None:
            self._client = httpx.AsyncClient(timeout=15.0)

        try:
            resp = await self._client.get(
                "https://people.googleapis.com/v1/people/me",
                headers={"Authorization": f"Bearer {token}"},
                params={
                    "personFields": "names,emailAddresses,phoneNumbers,photos,organizations",
                },
            )
            resp.raise_for_status()
            data = resp.json()
            names = data.get("names", [])
            name = names[0].get("displayName", "") if names else ""
            emails = data.get("emailAddresses", [])
            email = emails[0].get("value", "") if emails else ""
            phones = data.get("phoneNumbers", [])
            phone = phones[0].get("value", "") if phones else ""
            photos = data.get("photos", [])
            photo_url = photos[0].get("url", "") if photos else ""
            orgs = data.get("organizations", [])
            org = orgs[0].get("name", "") if orgs else ""
            output = []
            if name:
                output.append(f"Name: {name}")
            if email:
                output.append(f"Email: {email}")
            if phone:
                output.append(f"Phone: {phone}")
            if org:
                output.append(f"Organization: {org}")
            if photo_url:
                output.append(f"Photo: {photo_url}")
            return "\n".join(output) if output else "No profile information found"
        except Exception:
            return "Profile lookup failed"

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()


class Plugin(BasePlugin):
    @property
    def name(self) -> str:
        return "google_people"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Google People API for contacts and profile"

    def __init__(self) -> None:
        self._tools: list[BaseTool] = []

    def get_tools(self) -> list[BaseTool]:
        return self._tools

    async def initialize(self, config: dict | None = None) -> None:
        from app.core.config import get_settings

        settings = get_settings()
        if settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET:
            self._tools = [
                PeopleSearchTool(),
                PeopleProfileTool(),
            ]

    async def cleanup(self) -> None:
        for tool in self._tools:
            if hasattr(tool, "close"):
                await tool.close()
