from __future__ import annotations

import time
import uuid
from typing import Any

from app.core.logging import get_logger
from app.schemas.voice import VoiceSessionConfig

logger = get_logger(__name__)


class VoiceSession:
    def __init__(self, session_id: str, config: VoiceSessionConfig) -> None:
        self.session_id = session_id
        self.config = config
        self.created_at = time.monotonic()
        self.last_activity = self.created_at
        self.messages: list[dict[str, Any]] = []
        self.is_active = True

    def update_activity(self) -> None:
        self.last_activity = time.monotonic()

    def is_expired(self) -> bool:
        elapsed = (time.monotonic() - self.last_activity) * 1000
        return elapsed > self.config.max_session_duration_ms

    def add_message(self, role: str, content: str) -> None:
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": time.monotonic(),
        })
        self.update_activity()

    def get_history(self, limit: int = 20) -> list[dict[str, str]]:
        return [{"role": m["role"], "content": m["content"]} for m in self.messages[-limit:]]

    def close(self) -> None:
        self.is_active = False


class VoiceSessionManager:
    def __init__(self) -> None:
        self._sessions: dict[str, VoiceSession] = {}

    def create_session(
        self, config: VoiceSessionConfig | None = None
    ) -> VoiceSession:
        session_id = str(uuid.uuid4())
        cfg = config or VoiceSessionConfig()
        session = VoiceSession(session_id, cfg)
        self._sessions[session_id] = session
        logger.info("voice_session_created", session_id=session_id)
        return session

    def get_session(self, session_id: str) -> VoiceSession | None:
        session = self._sessions.get(session_id)
        if session and session.is_expired():
            session.close()
            del self._sessions[session_id]
            return None
        return session

    def close_session(self, session_id: str) -> bool:
        session = self._sessions.pop(session_id, None)
        if session:
            session.close()
            logger.info("voice_session_closed", session_id=session_id)
            return True
        return False

    def cleanup_expired(self) -> int:
        expired = [
            sid for sid, s in self._sessions.items()
            if s.is_expired()
        ]
        for sid in expired:
            del self._sessions[sid]
        return len(expired)

    def get_active_sessions(self) -> list[dict[str, Any]]:
        return [
            {
                "session_id": s.session_id,
                "created_at": s.created_at,
                "message_count": len(s.messages),
                "is_active": s.is_active,
            }
            for s in self._sessions.values()
            if s.is_active
        ]
