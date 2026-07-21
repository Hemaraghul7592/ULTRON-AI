# Voice Engine — ULTRON AI Platform

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Voice Engine                        │
│                                                     │
│  Audio Input ──► STT ──► Text ──► AI ──► TTS ──► Audio Output │
│                     │                │                      │
│                     ▼                ▼                      │
│              ┌──────────┐    ┌──────────┐                  │
│              │ Providers │    │ Providers│                  │
│              │ - Groq    │    │ - Groq   │                  │
│              │ - Gemini  │    │ - Gemini │                  │
│              └──────────┘    └──────────┘                  │
│                                                     │
│  ┌─────────────────────────────────────────────┐    │
│  │           Voice Session Manager              │    │
│  │  - WebSocket connection per session          │    │
│  │  - Streaming audio chunks                    │    │
│  │  - VAD (Voice Activity Detection)            │    │
│  │  - Session lifecycle (create → process → end)│    │
│  └─────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

## Speech-to-Text (STT)

### Providers

| Provider | Models | Languages | Real-time | Cost |
|----------|--------|-----------|-----------|------|
| Groq Whisper | `whisper-large-v3` | 99 | ✅ | Free tier |
| Gemini | `gemini-2.0-flash` | multilingual | ✅ | Included |
| Future: Whisper.cpp | local models | 99 | ✅ | Free |

### Implementation

```python
class STTProvider(ABC):
    @abstractmethod
    async def transcribe(self, audio: bytes, language: str | None = None) -> str: ...

    @abstractmethod
    async def transcribe_stream(self, audio_chunks: AsyncIterator[bytes]) -> AsyncIterator[str]: ...
```

## Text-to-Speech (TTS)

### Providers

| Provider | Voices | Streaming | Languages |
|----------|--------|-----------|-----------|
| Groq PlayAI | Multiple | ✅ | EN |
| Gemini | Built-in | ✅ | Multilingual |
| Future: Piper | Local | ✅ | 40+ |

## Voice Session Flow (WebSocket)

```
Client                     Server
  │                          │
  ├── WS /ws/voice─────────►│
  │◄── session_created ─────┤
  │                          │
  ├── audio_chunk ──────────►│
  ├── audio_chunk ──────────►│
  ├── audio_chunk ──────────►│
  │                          ├── STT → text
  │                          ├── AI → response
  │                          ├── TTS → audio
  │◄── audio_chunk ─────────┤
  │◄── audio_chunk ─────────┤
  │◄── audio_chunk ─────────┤
  │◄── session_complete ────┤
  │                          │
  ├── WS close ────────────►│
```

## Voice Conversation Mode

```
VAD detects speech ──► STT ──► AI processes ──► TTS ──► Play audio
       │                                                            │
       └─────────────────── Loop ───────────────────────────────────┘
```

### Wake Word (Future)

- Local wake word detection on client (Porcupine / Picovoice)
- Only streams to backend after wake word detected
- Privacy-preserving: no audio leaves device until activated

## Pipeline Latency Budget

```python
TARGET_END_TO_END_MS = 2000  # 2 seconds max

LATENCY_BUDGET = {
    "network_transport": 300,   # 300ms audio upload
    "stt": 500,                 # 500ms transcription
    "ai_generation": 800,       # 800ms first token
    "tts": 300,                 # 300ms audio generation
    "network_return": 100,      # 100ms audio download
}
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/voice/stt` | Transcribe audio file |
| POST | `/voice/tts` | Generate speech from text |
| WS | `/ws/voice` | Full-duplex voice session |
| POST | `/voice/session/create` | Create session config |
