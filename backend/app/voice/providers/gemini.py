from __future__ import annotations

import base64
from typing import Any

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger
from app.voice.errors import ProviderAuthError, SpeechRecognitionError, SpeechSynthesisError
from app.voice.interface import SpeechToTextProvider, STTResult, TextToSpeechProvider, TTSResult

logger = get_logger(__name__)


class GeminiSTTProvider(SpeechToTextProvider):
    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or get_settings().GEMINI_API_KEY
        self._client: httpx.AsyncClient | None = None

    @property
    def name(self) -> str:
        return "gemini_stt"

    async def transcribe(
        self,
        audio_data: bytes,
        language: str = "en-US",
        filename: str = "audio.wav",
    ) -> STTResult:
        if not self._api_key:
            raise ProviderAuthError(message="Gemini API key not configured", provider=self.name)
        try:
            audio_b64 = base64.b64encode(audio_data).decode()
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": f"Transcribe this audio. Language: {language}"},
                            {"inline_data": {"mime_type": "audio/wav", "data": audio_b64}},
                        ],
                    },
                ],
            }
            client = self._get_client()
            response = await client.post(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
                headers={"x-goog-api-key": self._api_key},
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            text = ""
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                for part in parts:
                    if "text" in part:
                        text = part["text"]
            return STTResult(
                text=text.strip(),
                confidence=0.9,
                language=language,
                duration_ms=0.0,
                provider=self.name,
            )
        except Exception as e:
            logger.error("gemini_stt_failed", error=str(e))
            raise SpeechRecognitionError(
                message=str(e), provider=self.name, original_error=e,
            ) from e

    async def validate(self) -> bool:
        return bool(self._api_key)

    async def health_check(self) -> dict[str, Any]:
        if not self._api_key:
            return {"status": "auth_failed", "provider": self.name}
        return {"status": "available", "provider": self.name}

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=60.0)
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None


class GeminiTTSProvider(TextToSpeechProvider):
    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or get_settings().GEMINI_API_KEY
        self._client: httpx.AsyncClient | None = None

    @property
    def name(self) -> str:
        return "gemini_tts"

    async def synthesize(
        self,
        text: str,
        voice_id: str | None = None,
        speed: float = 1.0,
        language: str = "en",
    ) -> TTSResult:
        if not self._api_key:
            raise ProviderAuthError(message="Gemini API key not configured", provider=self.name)
        try:
            payload = {
                "contents": [{"parts": [{"text": text}]}],
                "generationConfig": {
                    "responseModalities": ["AUDIO"],
                    "audioConfig": {"audioEncoding": "LINEAR16", "sampleRateHertz": 24000},
                },
            }
            client = self._get_client()
            response = await client.post(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-preview-tts:generateContent",
                headers={"x-goog-api-key": self._api_key},
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                for part in parts:
                    if "inlineData" in part:
                        audio_b64 = part["inlineData"].get("data", "")
                        return TTSResult(
                            audio_base64=audio_b64,
                            format="wav",
                            size_bytes=len(audio_b64) * 3 // 4,
                            provider=self.name,
                            voice_id=voice_id or "Kore",
                        )
            return TTSResult(provider=self.name, voice_id=voice_id or "Kore")
        except Exception as e:
            logger.error("gemini_tts_failed", error=str(e))
            raise SpeechSynthesisError(message=str(e), provider=self.name, original_error=e) from e

    async def validate(self) -> bool:
        return bool(self._api_key)

    async def health_check(self) -> dict[str, Any]:
        if not self._api_key:
            return {"status": "auth_failed", "provider": self.name}
        return {"status": "available", "provider": self.name}

    def supported_voices(self) -> list[str]:
        return ["Kore", "Puck", "Charon", "Fenrir"]

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=60.0)
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None
