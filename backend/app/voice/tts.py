from __future__ import annotations

import base64
from typing import Any

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class TextToSpeechService:
    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=60.0)
        return self._client

    async def synthesize(
        self,
        text: str,
        voice_id: str | None = None,
        speed: float = 1.0,
        language: str = "en",
    ) -> dict[str, Any]:
        settings = get_settings()
        if settings.GROQ_API_KEY:
            return await self._synthesize_groq(text, voice_id)
        if settings.GEMINI_API_KEY:
            return await self._synthesize_gemini(text, voice_id)

        logger.warning("no_tts_provider_available")
        return {"audio_base64": "", "format": "wav"}

    async def _synthesize_groq(
        self,
        text: str,
        voice_id: str | None,
    ) -> dict[str, Any]:
        settings = get_settings()
        try:
            selected = voice_id or "Arista"

            response = await self.client.post(
                "https://api.groq.com/openai/v1/audio/speech",
                headers={
                    "Authorization": f"Bearer {settings.GROQ_API_KEY}",
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
            audio_b64 = base64.b64encode(audio_data).decode()
            return {
                "audio_base64": audio_b64,
                "format": "wav",
                "size_bytes": len(audio_data),
            }
        except Exception as e:
            logger.error("groq_tts_failed", error=str(e))
            return {"audio_base64": "", "format": "wav"}

    async def _synthesize_gemini(
        self,
        text: str,
        voice_id: str | None,
    ) -> dict[str, Any]:
        settings = get_settings()
        try:
            payload = {
                "contents": [{"parts": [{"text": text}]}],
                "generationConfig": {
                    "responseModalities": ["AUDIO"],
                    "audioConfig": {
                        "audioEncoding": "LINEAR16",
                        "sampleRateHertz": 24000,
                    },
                },
            }
            model = "gemini-2.0-flash-preview-tts"
            response = await self.client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                headers={"x-goog-api-key": settings.GEMINI_API_KEY},
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                for part in parts:
                    if "inlineData" in part:
                        audio_data = part["inlineData"].get("data", "")
                        return {
                            "audio_base64": audio_data,
                            "format": "wav",
                            "size_bytes": len(audio_data) * 3 // 4,
                        }
            return {"audio_base64": "", "format": "wav"}
        except Exception as e:
            logger.error("gemini_tts_failed", error=str(e))
            return {"audio_base64": "", "format": "wav"}

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
