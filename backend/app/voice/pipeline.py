from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.voice.stt import SpeechToTextService
from app.voice.tts import TextToSpeechService
from app.voice.session import VoiceSessionManager, VoiceSession

logger = get_logger(__name__)


class VoicePipeline:
    def __init__(self) -> None:
        self.stt = SpeechToTextService()
        self.tts = TextToSpeechService()
        self.session_manager = VoiceSessionManager()
        self._chat_handler: Any = None

    def set_chat_handler(self, handler: Any) -> None:
        self._chat_handler = handler

    async def process_audio_input(
        self,
        session_id: str,
        audio_data: bytes | None = None,
        audio_base64: str | None = None,
        language: str = "en-US",
    ) -> dict[str, Any]:
        session = self.session_manager.get_session(session_id)
        if not session:
            session = self.session_manager.create_session()
            session_id = session.session_id

        stt_result = await self.stt.transcribe(
            audio_data=audio_data,
            audio_base64=audio_base64,
            language=language,
        )
        text = stt_result.get("text", "")
        if not text:
            return {
                "session_id": session_id,
                "user_text": "",
                "response_text": "",
                "audio_base64": None,
                "confidence": 0.0,
            }

        session.add_message("user", text)

        response_text = ""
        if self._chat_handler:
            chat_response = await self._chat_handler(
                message=text,
                conversation_id=None,
            )
            response_text = chat_response.get("message", "")

        if response_text:
            session.add_message("assistant", response_text)

        tts_result = await self.tts.synthesize(
            text=response_text,
            voice_id=session.config.voice_id,
            language=language,
        )

        return {
            "session_id": session_id,
            "user_text": text,
            "response_text": response_text,
            "audio_base64": tts_result.get("audio_base64"),
            "confidence": stt_result.get("confidence", 0.0),
        }

    async def process_text_input(
        self,
        session_id: str,
        text: str,
        voice_id: str | None = None,
    ) -> dict[str, Any]:
        session = self.session_manager.get_session(session_id)
        if not session:
            session = self.session_manager.create_session()
            session_id = session.session_id

        session.add_message("user", text)

        response_text = ""
        if self._chat_handler:
            chat_response = await self._chat_handler(
                message=text,
                conversation_id=None,
            )
            response_text = chat_response.get("message", "")

        if response_text:
            session.add_message("assistant", response_text)

        tts_result = await self.tts.synthesize(
            text=response_text,
            voice_id=voice_id or session.config.voice_id,
        )

        return {
            "session_id": session_id,
            "user_text": text,
            "response_text": response_text,
            "audio_base64": tts_result.get("audio_base64"),
        }

    async def close(self) -> None:
        await self.stt.close()
        await self.tts.close()
