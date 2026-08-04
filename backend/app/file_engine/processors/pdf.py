from __future__ import annotations

from typing import Any

from app.file_engine.interface import FileMetadata  # noqa: TC001
from app.file_engine.processors.base import Processor

PDF_EXTENSIONS: set[str] = {".pdf"}


class PDFProcessor(Processor):
    @property
    def name(self) -> str:
        return "pdf"

    def supported_extensions(self) -> set[str]:
        return PDF_EXTENSIONS

    async def extract_text(self, data: bytes, metadata: FileMetadata) -> str:
        return await self._extract_pdf_text(data)

    async def process(self, data: bytes, metadata: FileMetadata) -> FileMetadata:
        text = await self._extract_pdf_text(data)
        page_count = await self._count_pages(data)
        metadata.pages = page_count
        metadata.extra["char_count"] = len(text)
        metadata.extra["page_count"] = page_count
        return metadata

    async def extract_metadata(self, data: bytes, metadata: FileMetadata) -> dict[str, Any]:
        text = await self._extract_pdf_text(data)
        page_count = await self._count_pages(data)
        return {
            "char_count": len(text),
            "page_count": page_count,
            "has_text": bool(text.strip()),
        }

    async def _extract_pdf_text(self, data: bytes) -> str:
        try:
            text_parts: list[str] = []
            i = 0
            while i < len(data):
                stream_end = data.find(b"endstream", i)
                if stream_end == -1:
                    break
                stream_start = data.rfind(b"stream\n", i, stream_end)
                if stream_start == -1:
                    stream_start = data.rfind(b"stream ", i, stream_end)
                if stream_start == -1:
                    i = stream_end + 9
                    continue
                stream_start += (
                    len(b"stream\n")
                    if data[stream_start : stream_start + 7] == b"stream\n"
                    else len(b"stream ")
                )
                raw = data[stream_start:stream_end]
                try:
                    import zlib

                    decompressed = zlib.decompress(raw)
                    text_parts.append(self._extract_text_ops(decompressed))
                except Exception:
                    text_parts.append(self._extract_text_ops(raw))
                i = stream_end + 9

            result = "\n".join(text_parts)
            return result.strip()
        except Exception:
            return ""

    @staticmethod
    def _extract_text_ops(data: bytes) -> str:
        text_parts: list[str] = []
        i = 0
        in_paren = False
        current = ""
        while i < len(data):
            if not in_paren:
                if data[i] == ord("("):
                    in_paren = True
                    current = ""
                elif data[i] == ord("<") and i + 1 < len(data) and data[i + 1] == ord("<"):
                    i += 2
                    continue
                i += 1
            else:
                if data[i] == ord("\\"):
                    i += 1
                    if i < len(data):
                        current += chr(data[i])
                    i += 1
                elif data[i] == ord(")"):
                    in_paren = False
                    if current.strip():
                        text_parts.append(current.strip())
                    current = ""
                    i += 1
                else:
                    if 32 <= data[i] <= 126:
                        current += chr(data[i])
                    i += 1
        return " ".join(text_parts)

    async def _count_pages(self, data: bytes) -> int:
        try:
            text = data.decode("latin-1")
            count = 0
            i = 0
            while True:
                idx = text.find("/Type /Page", i)
                if idx == -1:
                    idx = text.find("/Type/Page", i)
                if idx == -1:
                    break
                count += 1
                i = idx + 1
            return max(count, 1)
        except Exception:
            return 1

    def validate(self, data: bytes, metadata: FileMetadata) -> bool:
        return data.startswith(b"%PDF")
