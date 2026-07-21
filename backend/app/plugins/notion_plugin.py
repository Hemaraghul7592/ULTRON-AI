from __future__ import annotations

from typing import Any

import httpx

from app.tools.base import BasePlugin, BaseTool


class NotionSearchTool(BaseTool):
    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        self._client: httpx.AsyncClient | None = None

    @property
    def name(self) -> str:
        return "search_notion"

    @property
    def description(self) -> str:
        return "Search Notion pages and databases"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "filter_type": {
                    "type": "string",
                    "enum": ["page", "database"],
                    "description": "Filter by type",
                },
            },
            "required": ["query"],
        }

    async def execute(self, **kwargs: Any) -> str:
        query = kwargs.get("query", "")
        filter_type = kwargs.get("filter_type")

        if not self._api_key:
            return "Notion API key not configured"

        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)

        try:
            payload: dict[str, Any] = {"query": query}
            if filter_type:
                payload["filter"] = {"value": filter_type, "property": "object"}

            resp = await self._client.post(
                "https://api.notion.com/v1/search",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Notion-Version": "2022-06-28",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results", [])
            if not results:
                return f"No results for '{query}'"
            output = [f"Found {len(results)} results:"]
            for r in results[:10]:
                obj_type = r.get("object", "")
                title = ""
                props = r.get("properties", {})
                for prop in props.values():
                    if prop.get("type") == "title":
                        title_parts = prop.get("title", [])
                        if title_parts:
                            title = title_parts[0].get("plain_text", "")
                        break
                if not title:
                    title = r.get("title", {}).get("plain_text", "Untitled")
                output.append(f"- [{obj_type}] {title}")
            return "\n".join(output)
        except Exception as e:
            return f"Notion search error: {e}"


class NotionReadPageTool(BaseTool):
    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        self._client: httpx.AsyncClient | None = None

    @property
    def name(self) -> str:
        return "read_notion_page"

    @property
    def description(self) -> str:
        return "Read content of a Notion page"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "page_id": {"type": "string", "description": "Notion page ID"},
            },
            "required": ["page_id"],
        }

    async def execute(self, **kwargs: Any) -> str:
        page_id = kwargs.get("page_id", "")
        if not self._api_key or not page_id:
            return "API key or page_id not provided"

        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)

        try:
            resp = await self._client.get(
                f"https://api.notion.com/v1/blocks/{page_id}/children",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Notion-Version": "2022-06-28",
                },
            )
            resp.raise_for_status()
            data = resp.json()
            blocks = data.get("results", [])
            content = []
            for block in blocks:
                btype = block.get("type", "")
                block_data = block.get(btype, {})
                rich_text = block_data.get("rich_text", [])
                text = "".join(rt.get("plain_text", "") for rt in rich_text)
                if text:
                    prefix = ""
                    if btype.startswith("heading"):
                        level = btype[-1]
                        prefix = "#" * int(level) + " "
                    elif btype == "bulleted_list_item":
                        prefix = "- "
                    elif btype == "numbered_list_item":
                        prefix = "1. "
                    elif btype == "to_do":
                        checked = block_data.get("checked", False)
                        prefix = "[x] " if checked else "[ ] "
                    content.append(f"{prefix}{text}")
            if not content:
                return "Page is empty or contains no text blocks"
            return "\n".join(content[:100])
        except Exception as e:
            return f"Notion read error: {e}"


class Plugin(BasePlugin):
    @property
    def name(self) -> str:
        return "notion"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Notion workspace integration"

    def __init__(self) -> None:
        self._tools: list[BaseTool] = []

    def get_tools(self) -> list[BaseTool]:
        return self._tools

    async def initialize(self, config: dict | None = None) -> None:
        from app.core.config import get_settings
        settings = get_settings()
        if settings.NOTION_API_KEY:
            self._tools = [
                NotionSearchTool(settings.NOTION_API_KEY),
                NotionReadPageTool(settings.NOTION_API_KEY),
            ]

    async def cleanup(self) -> None:
        for tool in self._tools:
            if hasattr(tool, "close"):
                await tool.close()
