from __future__ import annotations

import base64
from typing import Any

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class SpeechToTextService:
    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=60.0)
        return self._client

    async def transcribe(
        self,
        audio_data: bytes | None = None,
        audio_base64: str | None = None,
        language: str = "en-US",
        filename: str = "audio.wav",
    ) -> dict[str, Any]:
        settings = get_settings()
        if audio_base64 and not audio_data:
            audio_data = base64.b64decode(audio_base64)

        if not audio_data:
            return {"text": "", "confidence": 0.0, "language": language}

        if settings.GROQ_API_KEY:
            return await self._transcribe_groq(audio_data, filename, language)
        if settings.GEMINI_API_KEY:
            return await self._transcribe_gemini(audio_data, language)

        logger.warning("no_stt_provider_available")
        return {"text": "", "confidence": 0.0, "language": language}

    async def _transcribe_groq(
        self,
        audio_data: bytes,
        filename: str,
        language: str,
    ) -> dict[str, Any]:
        settings = get_settings()
        try:
            response = await self.client.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
                files={"file": (filename, audio_data, "audio/wav")},
                data={
                    "model": "whisper-large-v3-turbo",
                    "language": language[:2] if language else "en",
                    "response_format": "verbose_json",
                },
            )
            response.raise_for_status()
            data = response.json()
            return {
                "text": data.get("text", ""),
                "confidence": 0.95,
                "language": data.get("language", language),
                "duration_ms": data.get("duration", 0) * 1000,
            }
        except Exception as e:
            logger.error("groq_stt_failed", error=str(e))
            return {"text": "", "confidence": 0.0, "language": language}

    async def _transcribe_gemini(
        self,
        audio_data: bytes,
        language: str,
    ) -> dict[str, Any]:
        settings = get_settings()
        try:
            audio_b64 = base64.b64encode(audio_data).decode()
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": f"Transcribe this audio. Language: {language}"},
                            {
                                "inline_data": {
                                    "mime_type": "audio/wav",
                                    "data": audio_b64,
                                },
                            },
                        ],
                    },
                ],
            }
            response = await self.client.post(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
                headers={"x-goog-api-key": settings.GEMINI_API_KEY},
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
            return {
                "text": text.strip(),
                "confidence": 0.9,
                "language": language,
                "duration_ms": 0,
            }
        except Exception as e:
            logger.error("gemini_stt_failed", error=str(e))
            return {"text": "", "confidence": 0.0, "language": language}

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
