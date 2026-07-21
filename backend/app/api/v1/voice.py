from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.api.v1.auth import verify_token
from app.schemas.voice import VoiceRequest, VoiceResponse, VoiceSessionConfig
from app.voice.pipeline import VoicePipeline
from app.voice.session import VoiceSessionManager

router = APIRouter(prefix="/voice", tags=["voice"], dependencies=[Depends(verify_token)])

_fallback_session_manager: VoiceSessionManager | None = None
_fallback_pipeline: VoicePipeline | None = None


def _get_session_manager(request: Request) -> VoiceSessionManager:
    global _fallback_session_manager
    if hasattr(request.app.state, "voice_session_manager"):
        return request.app.state.voice_session_manager
    if _fallback_session_manager is None:
        _fallback_session_manager = VoiceSessionManager()
    return _fallback_session_manager


def _get_pipeline(request: Request) -> VoicePipeline:
    global _fallback_pipeline
    if hasattr(request.app.state, "voice_pipeline"):
        return request.app.state.voice_pipeline
    if _fallback_pipeline is None:
        _fallback_pipeline = VoicePipeline()
    return _fallback_pipeline


@router.post("/stt")
async def speech_to_text(request: VoiceRequest, pipeline: VoicePipeline = Depends(_get_pipeline)) -> VoiceResponse:
    result = await pipeline.stt.transcribe(
        audio_data=request.audio_data,
        audio_base64=request.audio_base64,
        language=request.language,
    )
    return VoiceResponse(
        text=result.get("text", ""),
        language=result.get("language", request.language),
        confidence=result.get("confidence", 0.0),
        duration_ms=result.get("duration_ms", 0),
    )


@router.post("/tts")
async def text_to_speech(request: VoiceRequest, pipeline: VoicePipeline = Depends(_get_pipeline)) -> VoiceResponse:
    result = await pipeline.tts.synthesize(
        text=request.text or "",
        voice_id=request.voice_id,
    )
    return VoiceResponse(
        text=request.text,
        audio_base64=result.get("audio_base64"),
    )


@router.post("/session/create")
async def create_voice_session(
    config: VoiceSessionConfig | None = None,
    session_manager: VoiceSessionManager = Depends(_get_session_manager),
) -> dict:
    session = session_manager.create_session(config)
    return {
        "session_id": session.session_id,
        "config": session.config.model_dump(),
    }


@router.post("/session/{session_id}/process")
async def process_voice(
    session_id: str,
    request: VoiceRequest,
    pipeline: VoicePipeline = Depends(_get_pipeline),
) -> dict:
    result = await pipeline.process_audio_input(
        session_id=session_id,
        audio_data=request.audio_data,
        audio_base64=request.audio_base64,
        language=request.language,
    )
    return result


@router.post("/session/{session_id}/process-text")
async def process_voice_text(
    session_id: str,
    request: VoiceRequest,
    pipeline: VoicePipeline = Depends(_get_pipeline),
) -> VoiceResponse:
    result = await pipeline.process_text_input(
        session_id=session_id,
        text=request.text or "",
        voice_id=request.voice_id,
    )
    return VoiceResponse(
        text=result.get("response_text", ""),
        audio_base64=result.get("audio_base64"),
    )


@router.delete("/session/{session_id}")
async def close_voice_session(
    session_id: str,
    session_manager: VoiceSessionManager = Depends(_get_session_manager),
) -> dict:
    closed = session_manager.close_session(session_id)
    return {"closed": closed}


@router.get("/sessions")
async def list_voice_sessions(
    session_manager: VoiceSessionManager = Depends(_get_session_manager),
) -> list[dict]:
    return session_manager.get_active_sessions()