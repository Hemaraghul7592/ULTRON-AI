# Voice Engine — ULTRON AI

## Architecture

```
VoiceService (single entry point)
        │
        ├── SpeechToTextProvider (interface)
        │       ├── GroqSTTProvider (Whisper via Groq)
        │       ├── GeminiSTTProvider (Gemini Flash)
        │       └── MockSTTProvider (testing)
        │
        ├── TextToSpeechProvider (interface)
        │       ├── GroqTTSProvider (playai-tts via Groq)
        │       ├── GeminiTTSProvider (Gemini Flash TTS)
        │       └── MockTTSProvider (testing)
        │
        ├── VoiceSession (session state + messages)
        │
        └── Audio Validation (format, size, MIME)
```

All voice interactions flow through `VoiceService`. No component calls STT/TTS providers directly.

## Core Files

| File | Purpose |
|------|---------|
| `app/voice/interface.py` | `SpeechToTextProvider` ABC, `TextToSpeechProvider` ABC, `STTResult`, `TTSResult` |
| `app/voice/errors.py` | `VoiceError` hierarchy (7 types) |
| `app/voice/service.py` | `VoiceService` — single entry point + `VoiceSession` |
| `app/voice/utils.py` | Audio validation, format detection, duration estimation |
| `app/voice/providers/groq.py` | `GroqSTTProvider` + `GroqTTSProvider` |
| `app/voice/providers/gemini.py` | `GeminiSTTProvider` + `GeminiTTSProvider` |
| `app/voice/providers/mock.py` | `MockSTTProvider` + `MockTTSProvider` |
| `app/voice/pipeline.py` | Backward-compatible `VoicePipeline` (unchanged) |
| `app/voice/stt.py` | Backward-compatible `SpeechToTextService` (unchanged) |
| `app/voice/tts.py` | Backward-compatible `TextToSpeechService` (unchanged) |
| `app/api/v1/voice.py` | REST API (prefers VoiceService, falls back to mock) |

## STT Provider Interface

| Method | Returns | Description |
|--------|---------|-------------|
| `transcribe(audio_data, language, filename)` | `STTResult` | Convert audio to text |
| `validate()` | `bool` | Check credentials |
| `health_check()` | `dict` | Provider status |
| `metadata()` | `dict` | Provider name + languages |
| `supported_languages()` | `list[str]` | Supported language codes |

## TTS Provider Interface

| Method | Returns | Description |
|--------|---------|-------------|
| `synthesize(text, voice_id, speed, language)` | `TTSResult` | Convert text to audio |
| `validate()` | `bool` | Check credentials |
| `health_check()` | `dict` | Provider status |
| `metadata()` | `dict` | Provider name + voices |
| `supported_voices()` | `list[str]` | Available voice IDs |

## VoiceService API

| Method | Description |
|--------|-------------|
| `transcribe(audio_data, audio_base64, language)` | Validate audio → STT provider → `STTResult` |
| `synthesize(text, voice_id, speed, language)` | TTS provider → `TTSResult` |
| `process(session_id, audio_data, audio_base64, language, voice_id)` | Full pipeline: STT → AI chat → TTS |
| `create_session(language)` | Create `VoiceSession` |
| `get_session(id)` | Look up session |
| `close_session(id)` | Close and remove session |
| `list_sessions()` | All active sessions |
| `health_check()` | STT + TTS health + active sessions |

## VoiceSession

| Field | Description |
|-------|-------------|
| `session_id` | UUID |
| `language` | Language code |
| `conversation_id` | Linked chat conversation |
| `created_at` | Creation timestamp |
| `last_activity` | Last interaction timestamp |
| `messages` | User/assistant message history |
| `status` | active / closed |

## Error Hierarchy

```
VoiceError
├── InvalidAudioError       — empty, too large, bad format
├── SpeechRecognitionError  — STT failure
├── SpeechSynthesisError    — TTS failure
├── SessionError            — session not found
├── ProviderUnavailableError
├── ProviderAuthError       — missing/invalid API key
```

## Audio Validation

- Max raw bytes: 25 MB
- Max base64: 35 MB
- Supported MIME types: wav, mpeg, mp4, ogg, flac
- Format auto-detection from header bytes
- WAV duration estimation from sample rate header

## Provider Selection

At startup, `main.py` selects providers:
1. If `GROQ_API_KEY` is set → Groq providers
2. Elif `GEMINI_API_KEY` is set → Gemini providers
3. Else → Mock providers (testing)

The API always falls back to mock providers if `app.state.voice_service` is unavailable.

## API Endpoints

All under `/api/v1/voice`, Bearer auth required.

| Method | Path | Description |
|--------|------|-------------|
| POST | `/voice/stt` | Speech to text |
| POST | `/voice/tts` | Text to speech |
| POST | `/voice/session/create` | Create voice session |
| POST | `/voice/session/{id}/process` | Full voice pipeline |
| DELETE | `/voice/session/{id}` | Close session |
| GET | `/voice/sessions` | List active sessions |
| GET | `/voice/health` | STT + TTS health |

## Tests

`tests/test_voice.py` — 45 tests covering:
- Provider interfaces (abstract, mock, health, validate)
- STTResult/TTSResult serialization
- VoiceSession lifecycle (create, message, close, to_dict)
- VoiceService (transcribe, synthesize, process, sessions, health, errors)
- Audio validation (format detection, size limits, base64)
- Error hierarchy
