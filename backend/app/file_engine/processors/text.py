from __future__ import annotations

from typing import Any

from app.file_engine.interface import FileMetadata  # noqa: TC001
from app.file_engine.processors.base import Processor
from app.file_engine.utils import TEXT_EXTENSIONS


class TextProcessor(Processor):
    @property
    def name(self) -> str:
        return "text"

    def supported_extensions(self) -> set[str]:
        return TEXT_EXTENSIONS

    async def extract_text(self, data: bytes, metadata: FileMetadata) -> str:
        try:
            return data.decode("utf-8")
        except UnicodeDecodeError:
            return data.decode("utf-8", errors="replace")

    async def process(self, data: bytes, metadata: FileMetadata) -> FileMetadata:
        text = await self.extract_text(data, metadata)
        metadata.extra["char_count"] = len(text)
        metadata.extra["line_count"] = text.count("\n") + 1
        return metadata

    async def extract_metadata(self, data: bytes, metadata: FileMetadata) -> dict[str, Any]:
        text = await self.extract_text(data, metadata)
        return {
            "char_count": len(text),
            "line_count": text.count("\n") + 1,
            "word_count": len(text.split()),
        }
