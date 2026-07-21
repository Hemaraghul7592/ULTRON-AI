from __future__ import annotations

from pydantic import BaseModel, field_validator

_MAX_AUDIO_BYTES = 25 * 1024 * 1024
_MAX_AUDIO_BASE64 = 35 * 1024 * 1024


class VoiceRequest(BaseModel):
    audio_data: bytes | None = None
    audio_base64: str | None = None
    language: str = "en-US"
    text: str | None = None
    voice_id: str | None = None

    @field_validator("audio_data")
    @classmethod
    def validate_audio_data_size(cls, v: bytes | None) -> bytes | None:
        if v is not None and len(v) > _MAX_AUDIO_BYTES:
            raise ValueError("Audio data exceeds maximum size of 25MB")
        return v

    @field_validator("audio_base64")
    @classmethod
    def validate_audio_base64_size(cls, v: str | None) -> str | None:
        if v is not None and len(v) > _MAX_AUDIO_BASE64:
            raise ValueError("Audio data exceeds maximum size")
        return v


class VoiceResponse(BaseModel):
    text: str | None = None
    audio_base64: str | None = None
    language: str = "en-US"
    confidence: float = 0.0
    duration_ms: float = 0.0


class WakeWordConfig(BaseModel):
    enabled: bool = False
    word: str = "hey ultron"
    sensitivity: float = 0.5
    audio_gain: float = 1.0


class VoiceSessionConfig(BaseModel):
    stt_enabled: bool = True
    tts_enabled: bool = True
    wake_word_enabled: bool = False
    language: str = "en-US"
    voice_id: str | None = None
    auto_respond: bool = True
    silence_timeout_ms: int = 3000
    max_session_duration_ms: int = 300000
