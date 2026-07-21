from __future__ import annotations

from typing import Any

import httpx

from app.tools.base import BasePlugin, BaseTool


class OCRSpaceTool(BaseTool):
    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        self._client: httpx.AsyncClient | None = None

    @property
    def name(self) -> str:
        return "ocr_extract_text"

    @property
    def description(self) -> str:
        return "Extract text from images or PDFs using OCR"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "image_url": {"type": "string", "description": "URL of the image"},
                "image_base64": {"type": "string", "description": "Base64 encoded image"},
                "language": {"type": "string", "default": "eng", "description": "OCR language"},
            },
        }

    async def execute(self, **kwargs: Any) -> str:
        image_url = kwargs.get("image_url", "")
        image_base64 = kwargs.get("image_base64", "")
        language = kwargs.get("language", "eng")

        if not self._api_key:
            return "OCR API key not configured"

        if self._client is None:
            self._client = httpx.AsyncClient(timeout=60.0)

        try:
            payload: dict[str, Any] = {
                "apikey": self._api_key,
                "language": language,
                "OCREngine": 2,
                "isOverlayRequired": False,
            }

            if image_base64:
                payload["base64Image"] = f"data:image/png;base64,{image_base64}"
            elif image_url:
                payload["url"] = image_url
            else:
                return "No image provided (provide image_url or image_base64)"

            resp = await self._client.post(
                "https://api.ocr.space/parse/image",
                data=payload,
            )
            resp.raise_for_status()
            data = resp.json()

            if data.get("IsErroredOnProcessing"):
                errors = data.get("ErrorMessage", ["Unknown error"])
                return f"OCR error: {errors}"

            parsed_results = data.get("ParsedResults", [])
            if not parsed_results:
                return "No text found in image"

            texts = []
            for result in parsed_results:
                text = result.get("ParsedText", "")
                if text:
                    texts.append(text)

            return "\n".join(texts)[:10000]
        except Exception as e:
            return f"OCR error: {e}"


class ImageReadTool(BaseTool):
    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        self._client: httpx.AsyncClient | None = None

    @property
    def name(self) -> str:
        return "read_image"

    @property
    def description(self) -> str:
        return "Read and extract text content from an image using OCR"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "image_url": {"type": "string", "description": "URL of the image to read"},
                "image_base64": {"type": "string", "description": "Base64 encoded image data"},
            },
        }

    async def execute(self, **kwargs: Any) -> str:
        image_url = kwargs.get("image_url", "")
        image_base64 = kwargs.get("image_base64", "")

        if not self._api_key:
            return "OCR API key not configured"

        if self._client is None:
            self._client = httpx.AsyncClient(timeout=60.0)

        try:
            payload: dict[str, Any] = {
                "apikey": self._api_key,
                "language": "eng",
                "OCREngine": 2,
                "isOverlayRequired": False,
            }

            if image_base64:
                payload["base64Image"] = f"data:image/png;base64,{image_base64}"
            elif image_url:
                payload["url"] = image_url
            else:
                return "No image provided"

            resp = await self._client.post(
                "https://api.ocr.space/parse/image",
                data=payload,
            )
            resp.raise_for_status()
            data = resp.json()

            parsed = data.get("ParsedResults", [])
            if not parsed:
                return "No text found in image"

            texts = [r.get("ParsedText", "") for r in parsed if r.get("ParsedText")]
            return "\n".join(texts)[:10000]
        except Exception as e:
            return f"Image read error: {e}"


class Plugin(BasePlugin):
    @property
    def name(self) -> str:
        return "ocr"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "OCR text extraction from images and documents"

    def __init__(self) -> None:
        self._tools: list[BaseTool] = []

    def get_tools(self) -> list[BaseTool]:
        return self._tools

    async def initialize(self, config: dict | None = None) -> None:
        from app.core.config import get_settings

        settings = get_settings()
        if settings.OCR_API_KEY:
            self._tools = [
                OCRSpaceTool(settings.OCR_API_KEY),
                ImageReadTool(settings.OCR_API_KEY),
            ]

    async def cleanup(self) -> None:
        for tool in self._tools:
            if hasattr(tool, "close"):
                await tool.close()
