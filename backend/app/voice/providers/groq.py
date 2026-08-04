from __future__ import annotations

import base64
from typing import Any

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger
from app.voice.errors import ProviderAuthError, SpeechRecognitionError, SpeechSynthesisError
from app.voice.interface import SpeechToTextProvider, STTResult, TextToSpeechProvider, TTSResult

logger = get_logger(__name__)


class GroqSTTProvider(SpeechToTextProvider):
    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or get_settings().GROQ_API_KEY
        self._client: httpx.AsyncClient | None = None

    @property
    def name(self) -> str:
        return "groq_stt"

    async def transcribe(
        self,
        audio_data: bytes,
        language: str = "en-US",
        filename: str = "audio.wav",
    ) -> STTResult:
        if not self._api_key:
            raise ProviderAuthError(message="Groq API key not configured", provider=self.name)
        try:
            client = self._get_client()
            response = await client.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {self._api_key}"},
                files={"file": (filename, audio_data, "audio/wav")},
                data={
                    "model": "whisper-large-v3-turbo",
                    "language": language[:2] if language else "en",
                    "response_format": "verbose_json",
                },
            )
            response.raise_for_status()
            data = response.json()
            return STTResult(
                text=data.get("text", ""),
                confidence=0.95,
                language=data.get("language", language),
                duration_ms=data.get("duration", 0.0) * 1000,
                provider=self.name,
            )
        except Exception as e:
            logger.error("groq_stt_failed", error=str(e))
            raise SpeechRecognitionError(
                message=str(e), provider=self.name, original_error=e,
            ) from e

    async def validate(self) -> bool:
        return bool(self._api_key)

    async def health_check(self) -> dict[str, Any]:
        if not self._api_key:
            return {"status": "auth_failed", "provider": self.name}
        return {"status": "available", "provider": self.name}

    def supported_languages(self) -> list[str]:
        return [
            "en",
            "en-US",
            "en-GB",
            "es",
            "fr",
            "de",
            "ja",
            "zh",
            "ko",
            "pt",
            "ru",
            "ar",
            "hi",
            "vi",
            "it",
            "nl",
            "tr",
            "pl",
            "sv",
            "id",
        ]

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=60.0)
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None


class GroqTTSProvider(TextToSpeechProvider):
    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or get_settings().GROQ_API_KEY
        self._client: httpx.AsyncClient | None = None

    @property
    def name(self) -> str:
        return "groq_tts"

    async def synthesize(
        self,
        text: str,
        voice_id: str | None = None,
        speed: float = 1.0,
        language: str = "en",
    ) -> TTSResult:
        if not self._api_key:
            raise ProviderAuthError(message="Groq API key not configured", provider=self.name)
        try:
            voices = self.supported_voices()
            selected = voice_id or voices[0] if voices else "Arista"
            client = self._get_client()
            response = await client.post(
                "https://api.groq.com/openai/v1/audio/speech",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "playai-tts",
                    "input": text,
                    "voice": selected,
                    "response_format": "wav",
                },
            )
            response.raise_for_status()
            audio_data = response.content
            return TTSResult(
                audio_base64=base64.b64encode(audio_data).decode(),
                format="wav",
                size_bytes=len(audio_data),
                provider=self.name,
                voice_id=selected,
            )
        except Exception as e:
            logger.error("groq_tts_failed", error=str(e))
            raise SpeechSynthesisError(message=str(e), provider=self.name, original_error=e) from e

    async def validate(self) -> bool:
        return bool(self._api_key)

    async def health_check(self) -> dict[str, Any]:
        if not self._api_key:
            return {"status": "auth_failed", "provider": self.name}
        return {"status": "available", "provider": self.name}

    def supported_voices(self) -> list[str]:
        return ["Arista", "Asteria", "Luna", "Stella", "Athena", "Perseus"]

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=60.0)
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None
