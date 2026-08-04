from __future__ import annotations

import abc
from typing import Any


class STTResult:
    def __init__(
        self,
        text: str = "",
        confidence: float = 0.0,
        language: str = "en-US",
        duration_ms: float = 0.0,
        provider: str = "",
    ) -> None:
        self.text = text
        self.confidence = confidence
        self.language = language
        self.duration_ms = duration_ms
        self.provider = provider

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "confidence": self.confidence,
            "language": self.language,
            "duration_ms": self.duration_ms,
            "provider": self.provider,
        }


class TTSResult:
    def __init__(
        self,
        audio_base64: str = "",
        format: str = "wav",  # noqa: A002
        size_bytes: int = 0,
        provider: str = "",
        voice_id: str = "",
    ) -> None:
        self.audio_base64 = audio_base64
        self.format = format  # noqa: A002
        self.size_bytes = size_bytes
        self.provider = provider
        self.voice_id = voice_id

    def to_dict(self) -> dict[str, Any]:
        return {
            "audio_base64": self.audio_base64,
            "format": self.format,
            "size_bytes": self.size_bytes,
            "provider": self.provider,
            "voice_id": self.voice_id,
        }


class SpeechToTextProvider(abc.ABC):
    @property
    @abc.abstractmethod
    def name(self) -> str:
        pass

    @abc.abstractmethod
    async def transcribe(
        self,
        audio_data: bytes,
        language: str = "en-US",
        filename: str = "audio.wav",
    ) -> STTResult:
        pass

    async def validate(self) -> bool:
        return True

    async def health_check(self) -> dict[str, Any]:
        return {"status": "available", "provider": self.name}

    def metadata(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "languages": self.supported_languages(),
        }

    def supported_languages(self) -> list[str]:
        return ["en-US", "en-GB", "es", "fr", "de", "ja", "zh", "ko"]


class TextToSpeechProvider(abc.ABC):
    @property
    @abc.abstractmethod
    def name(self) -> str:
        pass

    @abc.abstractmethod
    async def synthesize(
        self,
        text: str,
        voice_id: str | None = None,
        speed: float = 1.0,
        language: str = "en",
    ) -> TTSResult:
        pass

    async def validate(self) -> bool:
        return True

    async def health_check(self) -> dict[str, Any]:
        return {"status": "available", "provider": self.name}

    def metadata(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "voices": self.supported_voices(),
        }

    def supported_voices(self) -> list[str]:
        return ["default"]
