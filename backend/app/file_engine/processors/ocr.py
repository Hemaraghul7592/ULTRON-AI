from __future__ import annotations

import base64
from typing import Any

from app.file_engine.interface import FileMetadata
from app.file_engine.processors.base import Processor
from app.file_engine.processors.pdf import PDF_EXTENSIONS
from app.file_engine.utils import IMAGE_EXTENSIONS

OCR_EXTENSIONS: set[str] = IMAGE_EXTENSIONS | PDF_EXTENSIONS


class OCRProcessor(Processor):
    def __init__(self) -> None:
        self._enabled = False

    @property
    def name(self) -> str:
        return "ocr"

    def supported_extensions(self) -> set[str]:
        return OCR_EXTENSIONS

    async def process(self, data: bytes, metadata: FileMetadata) -> FileMetadata:
        try:
            text = await self._run_ocr(data, metadata)
            if text:
                metadata.ocr_text = text
                metadata.extra["ocr_text_length"] = len(text)
        except Exception:
            pass
        return metadata

    async def extract_text(self, data: bytes, metadata: FileMetadata) -> str:
        if metadata.ocr_text:
            return metadata.ocr_text
        try:
            return await self._run_ocr(data, metadata)
        except Exception:
            return ""

    async def _run_ocr(self, data: bytes, metadata: FileMetadata) -> str:
        try:
            from app.plugins.ocr_plugin import Plugin as OCRPlugin

            plugin = OCRPlugin()
            await plugin.initialize()
            tools = plugin.get_tools()
            if not tools:
                return ""

            b64 = base64.b64encode(data).decode("utf-8")
            result = await tools[0].execute(image_base64=b64)
            return result if isinstance(result, str) else ""
        except Exception:
            return ""

    async def extract_metadata(self, data: bytes, metadata: FileMetadata) -> dict[str, Any]:
        text = await self.extract_text(data, metadata)
        return {"has_ocr_text": bool(text), "ocr_text_length": len(text)}
