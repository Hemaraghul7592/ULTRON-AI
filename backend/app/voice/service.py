from __future__ import annotations

import time
import uuid
from typing import Any

from app.core.logging import get_logger
from app.voice.errors import (
    InvalidAudioError,
    SpeechRecognitionError,
    SpeechSynthesisError,
)
from app.voice.interface import (
    SpeechToTextProvider,
    STTResult,
    TextToSpeechProvider,
    TTSResult,
)
from app.voice.utils import validate_audio

logger = get_logger(__name__)


class VoiceSession:
    def __init__(self, session_id: str, language: str = "en-US") -> None:
        self.session_id = session_id
        self.language = language
        self.conversation_id: str | None = None
        self.created_at = time.time()
        self.last_activity = self.created_at
        self.messages: list[dict[str, Any]] = []
        self.status: str = "active"

    def add_message(self, role: str, content: str) -> None:
        self.messages.append({"role": role, "content": content, "timestamp": time.time()})
        self.update_activity()

    def update_activity(self) -> None:
        self.last_activity = time.time()

    def close(self) -> None:
        self.status = "closed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "language": self.language,
            "conversation_id": self.conversation_id,
            "created_at": self.created_at,
            "last_activity": self.last_activity,
            "message_count": len(self.messages),
            "status": self.status,
        }


class VoiceService:
    def __init__(
        self,
        stt_provider: SpeechToTextProvider,
        tts_provider: TextToSpeechProvider,
    ) -> None:
        self._stt = stt_provider
        self._tts = tts_provider
        self._sessions: dict[str, VoiceSession] = {}
        self._chat_handler: Any = None

    @property
    def stt(self) -> SpeechToTextProvider:
        return self._stt

    @property
    def tts(self) -> TextToSpeechProvider:
        return self._tts

    def set_chat_handler(self, handler: Any) -> None:
        self._chat_handler = handler

    async def create_session(self, language: str = "en-US") -> VoiceSession:
        sid = str(uuid.uuid4())
        session = VoiceSession(session_id=sid, language=language)
        self._sessions[sid] = session
        logger.info("voice_session_created", session_id=sid)
        return session

    def get_session(self, session_id: str) -> VoiceSession | None:
        return self._sessions.get(session_id)

    def close_session(self, session_id: str) -> bool:
        session = self._sessions.pop(session_id, None)
        if session:
            session.close()
            logger.info("voice_session_closed", session_id=session_id)
            return True
        return False

    def list_sessions(self) -> list[VoiceSession]:
        return list(self._sessions.values())

    async def transcribe(
        self,
        audio_data: bytes | None = None,
        audio_base64: str | None = None,
        language: str = "en-US",
        filename: str = "audio.wav",
    ) -> STTResult:
        try:
            if audio_base64 and not audio_data:
                import base64

                audio_data = base64.b64decode(audio_base64)

            if not audio_data:
                raise InvalidAudioError("No audio data provided")

            validate_audio(audio_data=audio_data)

            result = await self._stt.transcribe(
                audio_data=audio_data,
                language=language,
                filename=filename,
            )
            return result

        except InvalidAudioError:
            raise
        except SpeechRecognitionError:
            raise
        except Exception as e:
            raise SpeechRecognitionError(
                message=str(e),
                provider=self._stt.name,
                original_error=e,
            ) from e

    async def synthesize(
        self,
        text: str,
        voice_id: str | None = None,
        speed: float = 1.0,
        language: str = "en",
    ) -> TTSResult:
        if not text:
            return TTSResult(provider=self._tts.name)

        if len(text) > 5000:
            raise ValueError("Text too long for TTS (max 5000 characters)")

        try:
            result = await self._tts.synthesize(
                text=text,
                voice_id=voice_id,
                speed=speed,
                language=language,
            )
            return result

        except SpeechSynthesisError:
            raise
        except Exception as e:
            raise SpeechSynthesisError(
                message=str(e),
                provider=self._tts.name,
                original_error=e,
            ) from e

    async def process(
        self,
        session_id: str | None = None,
        audio_data: bytes | None = None,
        audio_base64: str | None = None,
        language: str = "en-US",
        voice_id: str | None = None,
    ) -> dict[str, Any]:
        if not session_id:
            session = await self.create_session(language)
            session_id = session.session_id
        else:
            session = self.get_session(session_id)
            if not session:
                session = await self.create_session(language)
                session_id = session.session_id

        stt_result = await self.transcribe(
            audio_data=audio_data,
            audio_base64=audio_base64,
            language=language,
        )

        user_text = stt_result.text
        if not user_text:
            return {
                "session_id": session_id,
                "user_text": "",
                "response_text": "",
                "audio_base64": None,
                "confidence": 0.0,
            }

        session.add_message("user", user_text)

        response_text = ""
        if self._chat_handler:
            try:
                chat_response = await self._chat_handler(
                    message=user_text,
                    conversation_id=session.conversation_id,
                )
                response_text = chat_response.get("message", "")
            except Exception as e:
                logger.error("chat_handler_error", error=str(e))

        if response_text:
            session.add_message("assistant", response_text)

        tts_result = await self.synthesize(
            text=response_text,
            voice_id=voice_id,
            language=language,
        )

        return {
            "session_id": session_id,
            "user_text": user_text,
            "response_text": response_text,
            "audio_base64": tts_result.audio_base64,
            "confidence": stt_result.confidence,
        }

    async def health_check(self) -> dict[str, Any]:
        stt_health = await self._stt.health_check()
        tts_health = await self._tts.health_check()
        valid = await self._stt.validate() and await self._tts.validate()
        return {
            "status": "healthy" if valid else "degraded",
            "stt": stt_health,
            "tts": tts_health,
            "active_sessions": len(self._sessions),
        }

    async def close(self) -> None:
        for session in self._sessions.values():
            session.close()
        self._sessions.clear()
        for provider in [self._stt, self._tts]:
            if hasattr(provider, "close"):
                await provider.close()
