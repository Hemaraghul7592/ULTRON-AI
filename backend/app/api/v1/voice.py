from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.api.v1.auth import verify_token
from app.schemas.voice import VoiceRequest, VoiceResponse, VoiceSessionConfig
from app.voice.providers.mock import MockSTTProvider, MockTTSProvider
from app.voice.service import VoiceService

router = APIRouter(prefix="/voice", tags=["voice"], dependencies=[Depends(verify_token)])

_fallback_service: VoiceService | None = None


def _get_voice_service(request: Request) -> VoiceService:
    global _fallback_service
    if hasattr(request.app.state, "voice_service"):
        return request.app.state.voice_service
    if _fallback_service is None:
        _fallback_service = VoiceService(
            stt_provider=MockSTTProvider(),
            tts_provider=MockTTSProvider(),
        )
    return _fallback_service


@router.post("/stt")
async def speech_to_text(
    request: VoiceRequest, vs: VoiceService = Depends(_get_voice_service),
) -> VoiceResponse:
    result = await vs.transcribe(
        audio_data=request.audio_data,
        audio_base64=request.audio_base64,
        language=request.language,
    )
    return VoiceResponse(
        text=result.text,
        language=result.language,
        confidence=result.confidence,
        duration_ms=result.duration_ms,
    )


@router.post("/tts")
async def text_to_speech(
    request: VoiceRequest, vs: VoiceService = Depends(_get_voice_service),
) -> VoiceResponse:
    result = await vs.synthesize(
        text=request.text or "",
        voice_id=request.voice_id,
    )
    return VoiceResponse(
        text=request.text,
        audio_base64=result.audio_base64,
    )


@router.post("/session/create")
async def create_voice_session(
    config: VoiceSessionConfig | None = None,
    vs: VoiceService = Depends(_get_voice_service),
) -> dict:
    session = await vs.create_session(language=config.language if config else "en-US")
    return {"session_id": session.session_id, "language": session.language}


@router.post("/session/{session_id}/process")
async def process_voice(
    session_id: str,
    request: VoiceRequest,
    vs: VoiceService = Depends(_get_voice_service),
) -> dict:
    return await vs.process(
        session_id=session_id,
        audio_data=request.audio_data,
        audio_base64=request.audio_base64,
        language=request.language,
        voice_id=request.voice_id,
    )


@router.delete("/session/{session_id}")
async def close_voice_session(
    session_id: str,
    vs: VoiceService = Depends(_get_voice_service),
) -> dict:
    return {"closed": vs.close_session(session_id)}


@router.get("/sessions")
async def list_voice_sessions(
    vs: VoiceService = Depends(_get_voice_service),
) -> list[dict]:
    return [s.to_dict() for s in vs.list_sessions()]


@router.get("/health")
async def voice_health(
    vs: VoiceService = Depends(_get_voice_service),
) -> dict:
    return await vs.health_check()
