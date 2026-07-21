from __future__ import annotations

from typing import Any

from app.file_engine.interface import FileMetadata
from app.file_engine.processors.base import Processor
from app.file_engine.utils import IMAGE_EXTENSIONS


class ImageProcessor(Processor):
    @property
    def name(self) -> str:
        return "image"

    def supported_extensions(self) -> set[str]:
        return IMAGE_EXTENSIONS

    async def extract_metadata(self, data: bytes, metadata: FileMetadata) -> dict[str, Any]:
        result: dict[str, Any] = {}

        if metadata.width:
            result["width"] = metadata.width
        if metadata.height:
            result["height"] = metadata.height

        if not metadata.width or not metadata.height:
            dims = self._get_dimensions(data)
            if dims:
                w, h = dims
                result["width"] = w
                result["height"] = h

        return result

    async def process(self, data: bytes, metadata: FileMetadata) -> FileMetadata:
        dims = self._get_dimensions(data)
        if dims:
            metadata.width, metadata.height = dims
        metadata.extra["has_alpha"] = self._check_alpha(metadata.mime_type)
        return metadata

    def _get_dimensions(self, data: bytes) -> tuple[int, int] | None:
        if len(data) < 32:
            return None
        try:
            if data.startswith(b"\x89PNG\r\n\x1a\n"):
                import struct

                w = struct.unpack(">I", data[16:20])[0]
                h = struct.unpack(">I", data[20:24])[0]
                return (w, h)
            if data.startswith(b"\xff\xd8"):
                return self._jpeg_dimensions(data)
            if data.startswith(b"GIF8"):
                import struct

                w = struct.unpack("<H", data[6:8])[0]
                h = struct.unpack("<H", data[8:10])[0]
                return (w, h)
            if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
                return self._webp_dimensions(data)
        except Exception:
            pass
        return None

    def _jpeg_dimensions(self, data: bytes) -> tuple[int, int] | None:
        i = 2
        while i < len(data) - 1:
            if data[i] != 0xFF:
                break
            marker = data[i + 1]
            if marker == 0xC0 or marker == 0xC2:
                if i + 9 < len(data):
                    h = (data[i + 5] << 8) | data[i + 6]
                    w = (data[i + 7] << 8) | data[i + 8]
                    return (w, h)
                break
            if marker == 0xD9:
                break
            if marker == 0xDA:
                break
            if i + 3 < len(data):
                length = ((data[i + 2] << 8) | data[i + 3]) + 2
                i += length
            else:
                break
        return None

    def _webp_dimensions(self, data: bytes) -> tuple[int, int] | None:
        if len(data) < 30:
            return None
        try:
            w = ((data[27] << 8) | data[26]) & 0x3FFF
            h = ((data[29] << 8) | data[28]) & 0x3FFF
            return (w, h)
        except Exception:
            return None

    @staticmethod
    def _check_alpha(mime_type: str) -> bool:
        return mime_type in ("image/png", "image/webp", "image/gif")

    async def extract_text(self, data: bytes, metadata: FileMetadata) -> str:
        return ""
