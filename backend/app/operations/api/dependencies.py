from __future__ import annotations

from fastapi import HTTPException, Request, status

from app.core.database import get_session
from app.operations.core.event_bus import InProcessEventBus
from app.operations.core.runtime import OperationsRuntime


def get_operations_runtime(request: Request) -> OperationsRuntime:
    runtime = getattr(request.app.state, "uaes_runtime", None)
    if runtime is None:
        try:
            runtime = OperationsRuntime(
                event_bus=InProcessEventBus(), session_factory=get_session(),
            )
        except RuntimeError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="UAES runtime is not initialized",
            ) from exc
        request.app.state.uaes_runtime = runtime
    return runtime
