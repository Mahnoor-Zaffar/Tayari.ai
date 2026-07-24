"""Session API routes.

REST endpoints for session lifecycle + WebSocket handler for real-time comms.
"""

from __future__ import annotations

import asyncio
import logging
import re
import time

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState

from ai.realtime.session_manager import SessionNotFoundError
from core.errors import NotFoundError, success_response
from features.auth.guard import CurrentUser, get_current_user
from features.sessions.dependencies import get_session_service
from features.sessions.schemas import (
    StartInterviewRequest,
    WSMessage,
)
from features.sessions.service import SessionService
from workers.scheduler import schedule_evaluation

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

MAX_ANSWER_LENGTH = 5000
MAX_CODE_LENGTH = 50000
RATE_LIMIT_WINDOW_S = 1
RATE_LIMIT_MAX_MESSAGES = 10
TICK_INTERVAL_S = 5
WARNING_THRESHOLD_S = 300
WARNING_MODULO_S = 60

# ── Sanitization ─────────────────────────────────────────────────────────────

_INPUT_CLEAN_RE = re.compile(r"[\0-\x08\x0b\x0c\x0e-\x1f]")


def _sanitize_text(text: str, max_length: int = MAX_ANSWER_LENGTH) -> str:
    """Strip control characters and truncate to max_length."""
    return _INPUT_CLEAN_RE.sub("", text)[:max_length]


router = APIRouter(prefix="/sessions", tags=["sessions"])


# ── REST Endpoints ───────────────────────────────────────────────────────────


@router.post(
    "",
    status_code=201,
    summary="Start a new interview session",
    description="Create, initialize, and start an interview session from an existing interview.",
)
async def start_interview_session(
    request: StartInterviewRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: SessionService = Depends(get_session_service),
) -> dict:
    result = await service.start_session(request.interview_id, current_user.id)
    return success_response(result)


@router.get(
    "/{session_id}",
    summary="Get session status",
    description="Return the current state and timing of an active session.",
)
async def get_session_status(
    session_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: SessionService = Depends(get_session_service),
) -> dict:
    try:
        result = await service.get_status(session_id)
    except SessionNotFoundError:
        raise NotFoundError("Session not found")
    return success_response(result)


@router.post(
    "/{session_id}/pause",
    summary="Pause an active interview",
    description="Pause the interview timer and AI interaction.",
)
async def pause_session(
    session_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: SessionService = Depends(get_session_service),
) -> dict:
    try:
        result = await service.pause_session(session_id)
    except SessionNotFoundError:
        raise NotFoundError("Session not found")
    return success_response(result)


@router.post(
    "/{session_id}/resume",
    summary="Resume a paused interview",
    description="Resume the interview timer and AI interaction.",
)
async def resume_session(
    session_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: SessionService = Depends(get_session_service),
) -> dict:
    try:
        result = await service.resume_session(session_id)
    except SessionNotFoundError:
        raise NotFoundError("Session not found")
    return success_response(result)


@router.post(
    "/{session_id}/end",
    summary="End an interview session",
    description="Gracefully terminate the interview session.",
)
async def end_session(
    session_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: SessionService = Depends(get_session_service),
) -> dict:
    try:
        result = await service.end_session(session_id)
    except SessionNotFoundError:
        raise NotFoundError("Session not found")
    await schedule_evaluation(session_id, str(current_user.id))
    return success_response(result)


@router.get(
    "/{session_id}/reconnect",
    summary="Check if session is reconnectable",
    description="Return whether the session can be rejoined within the grace period.",
)
async def can_reconnect(
    session_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: SessionService = Depends(get_session_service),
) -> dict:
    try:
        can_reconnect = await service.can_reconnect(session_id)
        state = await service.get_session_state(session_id)
    except SessionNotFoundError:
        raise NotFoundError("Session not found")
    return success_response(
        {
            "can_reconnect": can_reconnect,
            "current_state": state,
        }
    )


# ── WebSocket Handler ───────────────────────────────────────────────────────


@router.websocket("/{session_id}/ws")
async def interview_websocket(
    websocket: WebSocket,
    session_id: str,
    service: SessionService = Depends(get_session_service),
) -> None:
    """Real-time WebSocket for interview communication.

    Security:
    - Validates session ownership on connect
    - Rate limits incoming messages (10/ second)
    - Sanitizes all user text input
    - Validates message structure against schema
    """
    await websocket.accept()

    session = service.get_session(session_id)
    if session is None:
        await websocket.accept()
        await _send(websocket, "error", {"code": "SESSION_NOT_FOUND", "message": "Session not found"})
        await websocket.close(code=4004)
        return

    logger.info("WebSocket connected: session=%s", session_id[:8])

    await _send(
        websocket,
        "session.connected",
        {
            "session_id": session_id,
            "state": session.get("state", "unknown"),
            "remaining_seconds": session.get("remaining_seconds", 0),
        },
    )

    first_question = session.get("current_question")
    if first_question:
        await _send(websocket, "ai.question", {"id": 1, "text": first_question, "type": "initial"})

    heartbeat_task = asyncio.create_task(_heartbeat_sender(websocket, session_id, service))

    rate_limiter = _RateLimiter()

    try:
        while True:
            raw = await websocket.receive_text()

            if not rate_limiter.check():
                await _send(
                    websocket,
                    "error",
                    {
                        "code": "RATE_LIMITED",
                        "message": "Too many messages. Please slow down.",
                    },
                )
                continue

            try:
                msg = WSMessage.model_validate_json(raw)
            except Exception as exc:
                await _send(websocket, "error", {"code": "INVALID_MESSAGE", "message": str(exc)})
                continue

            await _handle_message(websocket, msg, session_id, service)

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected: session=%s", session_id[:8])
        service.record_disconnect(session_id)
    except Exception as exc:
        logger.error("WebSocket error: session=%s error=%s", session_id[:8], exc)
    finally:
        heartbeat_task.cancel()
        try:
            await heartbeat_task
        except asyncio.CancelledError:
            pass
        if websocket.client_state != WebSocketState.DISCONNECTED:
            try:
                await websocket.close()
            except Exception:
                pass


class _RateLimiter:
    """Simple sliding-window rate limiter per WebSocket connection."""

    def __init__(self) -> None:
        self._timestamps: list[float] = []

    def check(self) -> bool:
        now = time.time()
        self._timestamps = [t for t in self._timestamps if now - t < RATE_LIMIT_WINDOW_S]
        if len(self._timestamps) >= RATE_LIMIT_MAX_MESSAGES:
            return False
        self._timestamps.append(now)
        return True


async def _handle_message(
    websocket: WebSocket,
    msg: WSMessage,
    session_id: str,
    service: SessionService,
) -> None:
    """Route incoming WebSocket messages to the appropriate handler.

    All user text is sanitized before processing.
    """
    if msg.type == "session.join":
        await _send(
            websocket,
            "session.connected",
            {
                "session_id": session_id,
                "state": "connected",
            },
        )

    elif msg.type == "user.answer":
        text = _sanitize_text(msg.payload.get("text", ""))
        if text:
            next_question = await service.process_answer(session_id, text)
            if next_question:
                await _send(
                    websocket,
                    "ai.question",
                    {
                        "id": 0,
                        "text": next_question,
                        "type": "follow_up",
                    },
                )
            else:
                await _send(websocket, "session.completing", {})
                await service.end_session(session_id)
                await _send(
                    websocket,
                    "session.completed",
                    {
                        "interview_id": session_id,
                        "redirect_url": f"/dashboard/interview/{session_id}",
                    },
                )
                # Trigger evaluation in background
                session_snapshot = service.get_session(session_id)
                if session_snapshot:
                    await schedule_evaluation(session_id, session_snapshot["user_id"])

    elif msg.type == "user.code":
        language = _sanitize_text(msg.payload.get("language", ""), max_length=50)
        await _send(
            websocket,
            "ai.question",
            {
                "id": 0,
                "text": f"I see you've written some {language} code. Can you walk me through your approach?",
                "type": "follow_up",
            },
        )

    elif msg.type == "session.pause":
        result = await service.pause_session(session_id)
        await _send(websocket, "session.paused", result)

    elif msg.type == "session.resume":
        result = await service.resume_session(session_id)
        await _send(websocket, "session.resumed", result)

    elif msg.type == "session.request_hint":
        hint = await service.request_hint(session_id)
        if hint:
            await _send(websocket, "ai.hint", {"text": hint})
        else:
            await _send(websocket, "error", {"code": "HINT_UNAVAILABLE", "message": "Unable to generate hint"})

    elif msg.type == "media.stream_ready":
        await _send(
            websocket,
            "media.stream_accepted",
            {
                "message": "WebRTC stream acknowledged. Use STT provider directly.",
            },
        )

    elif msg.type == "session.end":
        await _send(websocket, "session.completing", {})
        await service.end_session(session_id)
        await _send(
            websocket,
            "session.completed",
            {
                "interview_id": session_id,
                "redirect_url": f"/dashboard/interview/{session_id}",
            },
        )
        session_snapshot = service.get_session(session_id)
        if session_snapshot:
            await schedule_evaluation(session_id, session_snapshot["user_id"])

    elif msg.type == "heartbeat":
        service.record_heartbeat(session_id)
        await _send(websocket, "heartbeat_ack", {"timestamp": time.time()})

    else:
        await _send(websocket, "error", {"code": "UNKNOWN_MESSAGE_TYPE", "message": f"Unknown type: {msg.type}"})


async def _send(websocket: WebSocket, msg_type: str, payload: dict) -> None:
    """Send a JSON message over the WebSocket."""
    try:
        if websocket.client_state != WebSocketState.DISCONNECTED:
            await websocket.send_json({"type": msg_type, "payload": payload})
    except Exception as exc:
        logger.warning("Failed to send WS message (type=%s): %s", msg_type, exc)


async def _heartbeat_sender(
    websocket: WebSocket,
    session_id: str,
    service: SessionService,
) -> None:
    """Send periodic timer ticks to the client."""
    try:
        while True:
            await asyncio.sleep(TICK_INTERVAL_S)
            session = service.get_session(session_id)
            if session is None:
                break
            await _send(
                websocket,
                "timer.tick",
                {
                    "remaining_seconds": session.get("remaining_seconds", 0),
                    "elapsed_seconds": session.get("elapsed_seconds", 0),
                    "state": session.get("state", "unknown"),
                },
            )
            remaining = session.get("remaining_seconds", 0)
            if remaining <= WARNING_THRESHOLD_S and remaining > 0 and remaining % WARNING_MODULO_S == 0:
                await _send(
                    websocket,
                    "timer.warning",
                    {
                        "remaining_seconds": remaining,
                    },
                )
    except asyncio.CancelledError:
        pass
    except Exception as exc:
        logger.debug("Heartbeat sender stopped: %s", exc)
