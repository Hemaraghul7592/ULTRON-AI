from __future__ import annotations

from typing import Any

from app.file_engine.interface import FileMetadata
from app.file_engine.processors.base import Processor
from app.file_engine.utils import AUDIO_EXTENSIONS


class AudioProcessor(Processor):
    @property
    def name(self) -> str:
        return "audio"

    def supported_extensions(self) -> set[str]:
        return AUDIO_EXTENSIONS

    async def extract_metadata(self, data: bytes, metadata: FileMetadata) -> dict[str, Any]:
        duration = self._estimate_duration(data, metadata)
        result: dict[str, Any] = {}
        if duration:
            result["duration_seconds"] = duration
        if metadata.mime_type:
            result["mime_type"] = metadata.mime_type
        return result

    async def process(self, data: bytes, metadata: FileMetadata) -> FileMetadata:
        duration = self._estimate_duration(data, metadata)
        if duration:
            metadata.duration = duration
        return metadata

    async def extract_text(self, data: bytes, metadata: FileMetadata) -> str:
        return ""

    @staticmethod
    def _estimate_duration(data: bytes, metadata: FileMetadata) -> float | None:
        if not data:
            return None
        mime = metadata.mime_type

        if mime == "audio/wav" and len(data) > 44:
            try:
                import struct
                sample_rate = struct.unpack("<I", data[24:28])[0]
                channels = struct.unpack("<H", data[22:24])[0]
                bits_per_sample = struct.unpack("<H", data[34:36])[0]
                if sample_rate > 0 and channels > 0 and bits_per_sample > 0:
                    data_size = len(data) - 44
                    bytes_per_second = sample_rate * channels * (bits_per_sample // 8)
                    if bytes_per_second > 0:
                        return data_size / bytes_per_second
            except Exception:
                pass

        if mime == "audio/mpeg" and len(data) > 100:
            avg_bitrate = 128000
            return (len(data) * 8) / avg_bitrate

        return None
