from __future__ import annotations

from typing import Any

import httpx

from app.tools.base import BasePlugin, BaseTool


class WeatherTool(BaseTool):
    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        self._client: httpx.AsyncClient | None = None

    @property
    def name(self) -> str:
        return "get_weather"

    @property
    def description(self) -> str:
        return "Get current weather and forecast for a location. Returns temperature, conditions, humidity, wind."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City name or coordinates (e.g., 'London' or '51.5074,-0.1278')",
                },
                "units": {
                    "type": "string",
                    "enum": ["metric", "imperial"],
                    "default": "metric",
                },
                "days": {
                    "type": "integer",
                    "description": "Number of forecast days (1-5)",
                    "default": 1,
                },
            },
            "required": ["location"],
        }

    async def execute(self, **kwargs: Any) -> str:
        location = kwargs.get("location", "")
        units = kwargs.get("units", "metric")
        days = kwargs.get("days", 1)

        if not self._api_key:
            return "Weather API key not configured"

        if self._client is None:
            self._client = httpx.AsyncClient(timeout=15.0)

        try:
            unit_param = "metric" if units == "metric" else "imperial"
            response = await self._client.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={
                    "q": location,
                    "appid": self._api_key,
                    "units": unit_param,
                },
            )
            response.raise_for_status()
            data = response.json()

            temp = data["main"]["temp"]
            feels_like = data["main"]["feels_like"]
            humidity = data["main"]["humidity"]
            description = data["weather"][0]["description"]
            wind_speed = data["wind"]["speed"]
            name = data["name"]

            unit_symbol = "°C" if units == "metric" else "°F"
            speed_unit = "m/s" if units == "metric" else "mph"

            result = (
                f"Weather in {name}:\n"
                f"Temperature: {temp}{unit_symbol} (feels like {feels_like}{unit_symbol})\n"
                f"Conditions: {description}\n"
                f"Humidity: {humidity}%\n"
                f"Wind: {wind_speed} {speed_unit}"
            )

            if days > 1:
                forecast_response = await self._client.get(
                    "https://api.openweathermap.org/data/2.5/forecast",
                    params={
                        "q": location,
                        "appid": self._api_key,
                        "units": unit_param,
                        "cnt": days * 8,
                    },
                )
                if forecast_response.status_code == 200:
                    forecast = forecast_response.json()
                    result += "\n\nForecast:"
                    for item in forecast.get("list", [])[: days * 2]:
                        dt = item["dt_txt"]
                        ftemp = item["main"]["temp"]
                        fdesc = item["weather"][0]["description"]
                        result += f"\n{dt}: {ftemp}{unit_symbol}, {fdesc}"

            return result
        except httpx.HTTPStatusError as e:
            return f"Weather API error: {e.response.status_code}"
        except Exception as e:
            return f"Weather lookup failed: {e}"

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()


class WeatherForecastTool(BaseTool):
    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        self._client: httpx.AsyncClient | None = None

    @property
    def name(self) -> str:
        return "get_weather_forecast"

    @property
    def description(self) -> str:
        return "Get a detailed multi-day weather forecast for a location."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City name"},
                "days": {"type": "integer", "default": 3, "description": "Number of days (1-5)"},
            },
            "required": ["location"],
        }

    async def execute(self, **kwargs: Any) -> str:
        location = kwargs.get("location", "")
        days = kwargs.get("days", 3)

        if not self._api_key:
            return "Weather API key not configured"

        if self._client is None:
            self._client = httpx.AsyncClient(timeout=15.0)

        try:
            response = await self._client.get(
                "https://api.openweathermap.org/data/2.5/forecast",
                params={
                    "q": location,
                    "appid": self._api_key,
                    "units": "metric",
                    "cnt": days * 8,
                },
            )
            response.raise_for_status()
            data = response.json()
            city = data.get("city", {}).get("name", location)
            forecasts = []
            for item in data.get("list", []):
                dt = item["dt_txt"]
                temp = item["main"]["temp"]
                desc = item["weather"][0]["description"]
                humidity = item["main"]["humidity"]
                rain = item.get("rain", {}).get("3h", 0)
                forecasts.append(
                    f"{dt}: {temp}°C, {desc}, humidity {humidity}%, rain {rain}mm",
                )
            return f"Forecast for {city}:\n" + "\n".join(forecasts)
        except Exception as e:
            return "Forecast failed"


class Plugin(BasePlugin):
    @property
    def name(self) -> str:
        return "weather"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Weather information using OpenWeatherMap API"

    def __init__(self) -> None:
        self._tools: list[BaseTool] = []

    def get_tools(self) -> list[BaseTool]:
        return self._tools

    async def initialize(self, config: dict | None = None) -> None:
        from app.core.config import get_settings

        settings = get_settings()
        api_key = settings.OPEN_WEATHER_API_KEY
        if api_key:
            self._tools = [
                WeatherTool(api_key),
                WeatherForecastTool(api_key),
            ]
        else:
            self._tools = []

    async def cleanup(self) -> None:
        for tool in self._tools:
            if hasattr(tool, "close"):
                await tool.close()
