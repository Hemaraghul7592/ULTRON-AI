from __future__ import annotations

import base64
from typing import Any

from app.voice.interface import SpeechToTextProvider, STTResult, TextToSpeechProvider, TTSResult


class MockSTTProvider(SpeechToTextProvider):
    def __init__(
        self,
        transcript: str = "mock transcription",
        confidence: float = 0.99,
    ) -> None:
        self._transcript = transcript
        self._confidence = confidence

    @property
    def name(self) -> str:
        return "mock_stt"

    async def transcribe(
        self,
        audio_data: bytes,
        language: str = "en-US",
        filename: str = "audio.wav",
    ) -> STTResult:
        return STTResult(
            text=self._transcript,
            confidence=self._confidence,
            language=language,
            duration_ms=0.0,
            provider=self.name,
        )

    async def validate(self) -> bool:
        return True

    async def health_check(self) -> dict[str, Any]:
        return {"status": "available", "provider": self.name}


class MockTTSProvider(TextToSpeechProvider):
    def __init__(self, output_base64: str = "") -> None:
        self._output_base64 = output_base64 or base64.b64encode(b"mock audio data").decode()

    @property
    def name(self) -> str:
        return "mock_tts"

    async def synthesize(
        self,
        text: str,
        voice_id: str | None = None,
        speed: float = 1.0,
        language: str = "en",
    ) -> TTSResult:
        return TTSResult(
            audio_base64=self._output_base64,
            format="wav",
            size_bytes=len(self._output_base64) * 3 // 4,
            provider=self.name,
            voice_id=voice_id or "mock_voice",
        )

    async def validate(self) -> bool:
        return True

    async def health_check(self) -> dict[str, Any]:
        return {"status": "available", "provider": self.name}

    def supported_voices(self) -> list[str]:
        return ["mock_voice", "mock_voice_2"]
