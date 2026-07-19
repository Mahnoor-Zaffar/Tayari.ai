"""Voice routes — transcription via Whisper and FunASR streaming."""

from __future__ import annotations

import asyncio
import json
import time

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel

from core.config import settings
from core.errors import success_response
from core.logging import get_logger
from features.auth.guard import CurrentUser, get_current_user

from .funasr_service import StreamingSession
from .whisper import TranscriptionError, transcribe_audio

router = APIRouter(tags=["voice"])
log = get_logger("voice")

# Rate limit: max 10 transcription requests per minute per user
_RATE_LIMIT_MAX = 10
_RATE_LIMIT_WINDOW = 60  # seconds
_rate_limits: dict[str, list[float]] = {}


class TranscriptionResponse(BaseModel):
    text: str
    language: str
    duration_ms: int


@router.post("/voice/transcribe", summary="Transcribe audio using Whisper")
async def transcribe(
    file: UploadFile = File(...),
    language: str | None = None,
    current_user: CurrentUser = Depends(get_current_user),
) -> dict:
    user_id = getattr(current_user, "id", "unknown")

    # Simple in-memory rate limiting
    now = time.time()
    user_requests = _rate_limits.setdefault(str(user_id), [])
    user_requests[:] = [t for t in user_requests if now - t < _RATE_LIMIT_WINDOW]
    if len(user_requests) >= _RATE_LIMIT_MAX:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Try again later.",
        )
    user_requests.append(now)

    # Read audio bytes
    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty audio file",
        )

    # Max 25MB (Whisper limit)
    max_bytes = 25 * 1024 * 1024
    if len(audio_bytes) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Audio file too large (max 25MB)",
        )

    filename = file.filename or "audio.webm"

    try:
        result = await transcribe_audio(
            audio_bytes,
            filename=filename,
            language=language,
        )
    except TranscriptionError as exc:
        log.error("Transcription failed for user %s: %s", user_id, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Transcription failed: {exc}",
        )

    return success_response(
        TranscriptionResponse(
            text=result["text"],
            language=result["language"],
            duration_ms=result["duration_ms"],
        ).model_dump()
    )


@router.get("/voice/config", summary="Get voice transcription config")
async def voice_config(
    current_user: CurrentUser = Depends(get_current_user),
) -> dict:
    return success_response(
        {
            "whisper_model": settings.WHISPER_MODEL,
            "language": settings.WHISPER_LANGUAGE,
            "supported_formats": ["webm", "wav", "mp3", "ogg"],
            "max_duration_seconds": 30,
            "streaming_available": True,
        }
    )


# ── FunASR Streaming WebSocket ───────────────────────────────────────────────


@router.websocket("/voice/stream")
async def voice_stream(websocket: WebSocket) -> None:
    """Real-time speech-to-text via FunASR.

    Protocol:
    1. Client connects
    2. Client sends JSON config: {"type": "start", "language": "en"}
    3. Client sends binary audio chunks (PCM 16-bit mono 16kHz)
    4. Server sends JSON results:
       - {"type": "partial", "text": "..."}  (interim)
       - {"type": "final", "text": "..."}    (confirmed)
       - {"type": "error", "message": "..."}
    5. Client sends {"type": "stop"} or closes the WebSocket
    """
    await websocket.accept()
    log.info("Voice stream connected")

    session: StreamingSession | None = None
    audio_queue: asyncio.Queue[bytes] = asyncio.Queue()

    try:
        # ── Wait for start config ─────────────────────────────────────
        raw = await asyncio.wait_for(websocket.receive_text(), timeout=10.0)
        config = json.loads(raw)

        if config.get("type") != "start":
            await websocket.send_json({"type": "error", "message": "Expected start message"})
            await websocket.close()
            return

        language = config.get("language", "en")
        session = StreamingSession(language=language)
        await session.start()
        await websocket.send_json({"type": "started", "language": language})
        log.info("Voice stream started: language=%s", language)

        # ── Process audio and stream results concurrently ─────────────
        async def _feed_audio():
            """Feed audio chunks from queue to FunASR session."""
            while True:
                chunk = await audio_queue.get()
                if chunk is None:
                    break
                await session.feed_audio(chunk)

        async def _send_results():
            """Send FunASR results back to client."""
            async for result in session.results():
                if result.error_message:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "message": result.error_message,
                        }
                    )
                elif result.text:
                    msg_type = "final" if result.is_final else "partial"
                    await websocket.send_json(
                        {
                            "type": msg_type,
                            "text": result.text,
                            "timestamp_ms": result.timestamp_ms,
                        }
                    )

        feed_task = asyncio.create_task(_feed_audio())
        result_task = asyncio.create_task(_send_results())

        # ── Main receive loop ─────────────────────────────────────────
        try:
            while True:
                message = await websocket.receive()

                if message.get("text"):
                    # JSON control message
                    data = json.loads(message["text"])
                    if data.get("type") == "stop":
                        break
                elif message.get("bytes"):
                    # Binary audio chunk
                    await audio_queue.put(message["bytes"])
        except WebSocketDisconnect:
            log.info("Voice stream disconnected by client")

    except TimeoutError:
        await websocket.send_json({"type": "error", "message": "Start timeout"})
    except json.JSONDecodeError:
        await websocket.send_json({"type": "error", "message": "Invalid JSON"})
    except Exception:
        log.exception("Voice stream error")
        try:
            await websocket.send_json({"type": "error", "message": "Internal error"})
        except Exception:
            pass
    finally:
        # Clean up
        if session:
            await session.close()
        await audio_queue.put(None)  # Signal feed task to stop

        # Wait for tasks to finish
        for task in [feed_task, result_task]:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        log.info("Voice stream closed")
