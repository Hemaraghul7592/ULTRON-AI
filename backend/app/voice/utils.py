from __future__ import annotations

import struct

MAX_AUDIO_BYTES = 25 * 1024 * 1024
MAX_AUDIO_BASE64 = 35 * 1024 * 1024
ALLOWED_MIME_TYPES: set[str] = {
    "audio/wav",
    "audio/x-wav",
    "audio/mpeg",
    "audio/mp4",
    "audio/ogg",
    "audio/flac",
}
ALLOWED_EXTENSIONS: set[str] = {
    ".wav", ".mp3", ".m4a", ".ogg", ".flac",
}


def validate_audio(
    audio_data: bytes | None = None,
    audio_base64: str | None = None,
    mime_type: str = "audio/wav",
) -> None:
    from app.voice.errors import InvalidAudioError

    if audio_base64 and not audio_data:
        import base64
        if len(audio_base64) > MAX_AUDIO_BASE64:
            raise InvalidAudioError(f"Audio base64 exceeds {MAX_AUDIO_BASE64} bytes")
        try:
            audio_data = base64.b64decode(audio_base64)
        except Exception:
            raise InvalidAudioError("Invalid base64 audio data")

    if not audio_data or len(audio_data) == 0:
        raise InvalidAudioError("Audio data is empty")

    if len(audio_data) > MAX_AUDIO_BYTES:
        raise InvalidAudioError(f"Audio exceeds {MAX_AUDIO_BYTES} bytes")

    if mime_type not in ALLOWED_MIME_TYPES and mime_type != "audio/wav":
        raise InvalidAudioError(f"Unsupported audio format: {mime_type}")


def get_audio_format(audio_data: bytes) -> str:
    if len(audio_data) < 4:
        return "unknown"
    if audio_data.startswith(b"RIFF") and audio_data[8:12] == b"WAVE":
        return "wav"
    if audio_data.startswith(b"\xff\xfb") or audio_data.startswith(b"\xff\xf3") or audio_data.startswith(b"\xff\xf2"):
        return "mp3"
    if audio_data.startswith(b"\xff\xf1") or audio_data.startswith(b"ID3"):
        return "mp3"
    if audio_data.startswith(b"OggS"):
        return "ogg"
    if audio_data.startswith(b"fLaC"):
        return "flac"
    return "unknown"


def estimate_audio_duration(audio_data: bytes, format: str) -> float:
    if format == "wav" and len(audio_data) > 44:
        try:
            sample_rate = struct.unpack("<I", audio_data[24:28])[0]
            channels = struct.unpack("<H", audio_data[22:24])[0]
            bits_per_sample = struct.unpack("<H", audio_data[34:36])[0]
            if sample_rate > 0 and channels > 0 and bits_per_sample > 0:
                data_size = len(audio_data) - 44
                bytes_per_second = sample_rate * channels * (bits_per_sample // 8)
                if bytes_per_second > 0:
                    return data_size / bytes_per_second
        except Exception:
            pass
    if format == "mp3":
        return len(audio_data) / (128 * 1000 / 8)
    return 0.0
