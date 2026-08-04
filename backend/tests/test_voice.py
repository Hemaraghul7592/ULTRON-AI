from __future__ import annotations

import base64
import uuid

import pytest

from app.voice.errors import (
    InvalidAudioError,
    ProviderUnavailableError,
    SessionError,
    SpeechRecognitionError,
    SpeechSynthesisError,
    VoiceError,
)
from app.voice.interface import SpeechToTextProvider, STTResult, TextToSpeechProvider, TTSResult
from app.voice.providers.mock import MockSTTProvider, MockTTSProvider
from app.voice.service import VoiceService, VoiceSession
from app.voice.utils import (
    estimate_audio_duration,
    get_audio_format,
    validate_audio,
)


class TestProviderInterfaces:
    def test_stt_provider_abstract(self) -> None:
        with pytest.raises(TypeError):

            class _(SpeechToTextProvider):  # type: ignore
                pass

            _()

    def test_tts_provider_abstract(self) -> None:
        with pytest.raises(TypeError):

            class _(TextToSpeechProvider):  # type: ignore
                pass

            _()

    def test_stt_provider_with_name(self) -> None:
        class P(SpeechToTextProvider):
            @property
            def name(self) -> str:
                return "test"

            async def transcribe(
                self, audio_data: bytes, language: str = "en-US", filename: str = "audio.wav",
            ) -> STTResult:
                return STTResult(text="ok", provider=self.name)

        p = P()
        assert p.name == "test"


class TestSTTResult:
    def test_default_values(self) -> None:
        r = STTResult()
        assert r.text == ""
        assert r.confidence == 0.0
        assert r.language == "en-US"

    def test_to_dict(self) -> None:
        r = STTResult(text="hello", confidence=0.95, language="fr", provider="test")
        d = r.to_dict()
        assert d["text"] == "hello"
        assert d["confidence"] == 0.95
        assert d["language"] == "fr"
        assert d["provider"] == "test"


class TestTTSResult:
    def test_default_values(self) -> None:
        r = TTSResult()
        assert r.audio_base64 == ""
        assert r.format == "wav"

    def test_to_dict(self) -> None:
        r = TTSResult(audio_base64="b64data", format="mp3", provider="test")
        d = r.to_dict()
        assert d["audio_base64"] == "b64data"
        assert d["format"] == "mp3"
        assert d["provider"] == "test"


class TestMockProviders:
    @pytest.mark.asyncio
    async def test_mock_stt(self) -> None:
        p = MockSTTProvider()
        result = await p.transcribe(b"audio data")
        assert result.text == "mock transcription"
        assert result.confidence == 0.99
        assert result.provider == "mock_stt"
        assert await p.validate() is True

    @pytest.mark.asyncio
    async def test_mock_stt_custom(self) -> None:
        p = MockSTTProvider(transcript="custom text", confidence=0.5)
        result = await p.transcribe(b"data")
        assert result.text == "custom text"
        assert result.confidence == 0.5

    @pytest.mark.asyncio
    async def test_mock_tts(self) -> None:
        p = MockTTSProvider()
        result = await p.synthesize("hello")
        assert result.format == "wav"
        assert len(result.audio_base64) > 0
        assert result.provider == "mock_tts"
        assert await p.validate() is True

    @pytest.mark.asyncio
    async def test_mock_tts_voices(self) -> None:
        p = MockTTSProvider()
        voices = p.supported_voices()
        assert "mock_voice" in voices
        assert len(voices) == 2

    @pytest.mark.asyncio
    async def test_mock_provider_health(self) -> None:
        p = MockSTTProvider()
        hc = await p.health_check()
        assert hc["status"] == "available"


class TestAudioValidation:
    def test_validate_empty_raises(self) -> None:
        with pytest.raises(InvalidAudioError):
            validate_audio(audio_data=b"")

    def test_validate_too_large(self) -> None:
        with pytest.raises(InvalidAudioError):
            validate_audio(audio_data=b"\x00" * (30 * 1024 * 1024))

    def test_validate_valid_data_passes(self) -> None:
        validate_audio(audio_data=b"fake wav data")

    def test_validate_bad_base64(self) -> None:
        with pytest.raises(InvalidAudioError):
            validate_audio(audio_base64="not valid base64!!!")

    def test_get_audio_format_wav(self) -> None:
        fmt = get_audio_format(b"RIFF\x00\x00\x00\x00WAVE")
        assert fmt == "wav"

    def test_get_audio_format_mp3(self) -> None:
        fmt = get_audio_format(b"\xff\xfb\x50\x00" + b"\x00" * 20)
        assert fmt == "mp3"

    def test_get_audio_format_ogg(self) -> None:
        fmt = get_audio_format(b"OggS" + b"\x00" * 20)
        assert fmt == "ogg"

    def test_get_audio_format_unknown(self) -> None:
        fmt = get_audio_format(b"\x00\x01\x02")
        assert fmt == "unknown"

    def test_estimate_duration_default(self) -> None:
        dur = estimate_audio_duration(b"\x00" * 100, "unknown")
        assert dur == 0.0


class TestVoiceSession:
    def test_create_session(self) -> None:
        sid = str(uuid.uuid4())
        s = VoiceSession(session_id=sid, language="fr")
        assert s.session_id == sid
        assert s.language == "fr"
        assert s.status == "active"

    def test_add_message(self) -> None:
        s = VoiceSession(session_id="s1")
        s.add_message("user", "hello")
        assert len(s.messages) == 1
        assert s.messages[0]["role"] == "user"
        assert s.messages[0]["content"] == "hello"

    def test_close(self) -> None:
        s = VoiceSession(session_id="s1")
        s.close()
        assert s.status == "closed"

    def test_to_dict(self) -> None:
        s = VoiceSession(session_id="s1")
        s.add_message("user", "hi")
        d = s.to_dict()
        assert d["session_id"] == "s1"
        assert d["status"] == "active"
        assert d["message_count"] == 1

    def test_update_activity(self) -> None:
        s = VoiceSession(session_id="s1")
        old = s.last_activity
        s.update_activity()
        assert s.last_activity >= old


class TestVoiceService:
    @pytest.fixture
    def svc(self) -> VoiceService:
        return VoiceService(
            stt_provider=MockSTTProvider(),
            tts_provider=MockTTSProvider(),
        )

    @pytest.mark.asyncio
    async def test_create_session(self, svc: VoiceService) -> None:
        s = await svc.create_session()
        assert s.status == "active"
        assert len(s.session_id) > 0

    @pytest.mark.asyncio
    async def test_close_session(self, svc: VoiceService) -> None:
        s = await svc.create_session()
        assert svc.close_session(s.session_id) is True
        assert svc.get_session(s.session_id) is None

    @pytest.mark.asyncio
    async def test_close_nonexistent(self, svc: VoiceService) -> None:
        assert svc.close_session("nope") is False

    @pytest.mark.asyncio
    async def test_list_sessions(self, svc: VoiceService) -> None:
        await svc.create_session()
        await svc.create_session()
        assert len(svc.list_sessions()) == 2

    @pytest.mark.asyncio
    async def test_transcribe_empty(self, svc: VoiceService) -> None:
        with pytest.raises(InvalidAudioError):
            await svc.transcribe(audio_data=b"")

    @pytest.mark.asyncio
    async def test_transcribe_success(self, svc: VoiceService) -> None:
        result = await svc.transcribe(audio_data=b"test audio data")
        assert result.text == "mock transcription"
        assert result.confidence > 0

    @pytest.mark.asyncio
    async def test_transcribe_base64(self, svc: VoiceService) -> None:
        b64 = base64.b64encode(b"test audio").decode()
        result = await svc.transcribe(audio_base64=b64)
        assert result.text == "mock transcription"

    @pytest.mark.asyncio
    async def test_synthesize_success(self, svc: VoiceService) -> None:
        result = await svc.synthesize("hello world")
        assert result.format == "wav"
        assert len(result.audio_base64) > 0

    @pytest.mark.asyncio
    async def test_synthesize_empty(self, svc: VoiceService) -> None:
        result = await svc.synthesize("")
        assert result.audio_base64 == ""

    @pytest.mark.asyncio
    async def test_process_full(self, svc: VoiceService) -> None:
        svc.set_chat_handler(async_mock_chat)
        b64 = base64.b64encode(b"test audio data").decode()
        result = await svc.process(audio_base64=b64, language="en-US")
        assert result["user_text"] == "mock transcription"
        assert "AI:" in result["response_text"]
        assert result["audio_base64"] is not None
        assert result["confidence"] > 0

    @pytest.mark.asyncio
    async def test_process_with_session(self, svc: VoiceService) -> None:
        svc.set_chat_handler(async_mock_chat)
        s = await svc.create_session()
        b64 = base64.b64encode(b"test").decode()
        result = await svc.process(session_id=s.session_id, audio_base64=b64)
        assert result["session_id"] == s.session_id

    @pytest.mark.asyncio
    async def test_process_no_audio(self, svc: VoiceService) -> None:
        with pytest.raises(InvalidAudioError):
            await svc.process()

    @pytest.mark.asyncio
    async def test_health_check(self, svc: VoiceService) -> None:
        health = await svc.health_check()
        assert health["status"] == "healthy"
        assert "stt" in health
        assert "tts" in health
        assert health["active_sessions"] >= 0

    @pytest.mark.asyncio
    async def test_health_with_sessions(self, svc: VoiceService) -> None:
        await svc.create_session()
        health = await svc.health_check()
        assert health["active_sessions"] == 1

    @pytest.mark.asyncio
    async def test_close(self, svc: VoiceService) -> None:
        await svc.create_session()
        await svc.close()
        assert len(svc.list_sessions()) == 0

    @pytest.mark.asyncio
    async def test_process_with_failing_stt(self) -> None:
        p = MockSTTProvider()
        p.transcribe = lambda audio_data, language="en-US", filename="audio.wav": (
            _ for _ in ()
        ).throw(  # type: ignore
            SpeechRecognitionError("fail"),
        )
        svc = VoiceService(stt_provider=p, tts_provider=MockTTSProvider())
        with pytest.raises(SpeechRecognitionError):
            await svc.transcribe(audio_data=b"test")

    @pytest.mark.asyncio
    async def test_process_with_failing_tts(self) -> None:
        p = MockTTSProvider()
        p.synthesize = lambda text, voice_id=None, speed=1.0, language="en": (_ for _ in ()).throw(  # type: ignore
            SpeechSynthesisError("fail"),
        )
        svc = VoiceService(stt_provider=MockSTTProvider(), tts_provider=p)
        with pytest.raises(SpeechSynthesisError):
            await svc.synthesize("test")


async def async_mock_chat(**kwargs: str) -> dict:
    return {"message": f"AI: {kwargs.get('message', '')}", "conversation_id": "conv_1"}


class TestVoiceErrors:
    def test_error_hierarchy(self) -> None:
        e1 = InvalidAudioError("bad audio")
        assert isinstance(e1, VoiceError)

        e2 = SpeechRecognitionError("recognition fail")
        assert isinstance(e2, VoiceError)

        e3 = SpeechSynthesisError("synthesis fail")
        assert isinstance(e3, VoiceError)

        e4 = SessionError("session fail")
        assert isinstance(e4, VoiceError)

        e5 = ProviderUnavailableError("provider down")
        assert isinstance(e5, VoiceError)

    def test_error_attributes(self) -> None:
        e = SpeechRecognitionError("msg", provider="test", original_error=ValueError("orig"))
        assert str(e) == "msg"
        assert e.provider == "test"
        assert e.original_error is not None
