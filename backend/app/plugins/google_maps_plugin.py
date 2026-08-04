from __future__ import annotations

from typing import Any

import httpx

from app.tools.base import BasePlugin, BaseTool


class GeocodeTool(BaseTool):
    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        self._client: httpx.AsyncClient | None = None

    @property
    def name(self) -> str:
        return "geocode_address"

    @property
    def description(self) -> str:
        return "Convert an address to geographic coordinates using Google Geocoding API"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "address": {"type": "string", "description": "Street address or place name"},
            },
            "required": ["address"],
        }

    async def execute(self, **kwargs: Any) -> str:
        address = kwargs.get("address", "")
        if not self._api_key:
            return "Google Maps API key not configured"
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=15.0)
        try:
            resp = await self._client.get(
                "https://maps.googleapis.com/maps/api/geocode/json",
                params={"address": address, "key": self._api_key},
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get("status") != "OK":
                return f"Geocoding failed: {data.get('status')}"
            results = data.get("results", [])
            if not results:
                return f"No results for '{address}'"
            loc = results[0]["geometry"]["location"]
            formatted = results[0]["formatted_address"]
            return f"{formatted}\nLatitude: {loc['lat']}, Longitude: {loc['lng']}"
        except Exception:
            return "Geocoding failed"

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()


class PlacesSearchTool(BaseTool):
    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        self._client: httpx.AsyncClient | None = None

    @property
    def name(self) -> str:
        return "search_places"

    @property
    def description(self) -> str:
        return "Search for places using Google Places API"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Place search query"},
                "location": {"type": "string", "description": "Latitude,longitude to bias results"},
                "radius": {
                    "type": "integer",
                    "default": 5000,
                    "description": "Search radius in meters",
                },
            },
            "required": ["query"],
        }

    async def execute(self, **kwargs: Any) -> str:
        query = kwargs.get("query", "")
        location = kwargs.get("location", "")
        radius = kwargs.get("radius", 5000)
        if not self._api_key:
            return "Google Maps API key not configured"
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=15.0)
        try:
            params: dict[str, Any] = {"query": query, "key": self._api_key}
            if location:
                params["location"] = location
                params["radius"] = radius
            resp = await self._client.get(
                "https://maps.googleapis.com/maps/api/place/textsearch/json",
                params=params,
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get("status") != "OK":
                return f"Places search failed: {data.get('status')}"
            results = data.get("results", [])
            if not results:
                return f"No places found for '{query}'"
            output = [f"Found {len(results)} places:"]
            for place in results[:5]:
                name = place.get("name", "Unknown")
                address = place.get("formatted_address", "")
                rating = place.get("rating", "N/A")
                output.append(f"- {name} ({address}) Rating: {rating}")
            return "\n".join(output)
        except Exception:
            return "Places search failed"

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()


class Plugin(BasePlugin):
    @property
    def name(self) -> str:
        return "google_maps"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Google Maps geocoding and places search"

    def __init__(self) -> None:
        self._tools: list[BaseTool] = []

    def get_tools(self) -> list[BaseTool]:
        return self._tools

    async def initialize(self, config: dict | None = None) -> None:
        from app.core.config import get_settings

        settings = get_settings()
        if settings.GOOGLE_MAPS_API_KEY:
            self._tools = [
                GeocodeTool(settings.GOOGLE_MAPS_API_KEY),
                PlacesSearchTool(settings.GOOGLE_MAPS_API_KEY),
            ]

    async def cleanup(self) -> None:
        for tool in self._tools:
            if hasattr(tool, "close"):
                await tool.close()
