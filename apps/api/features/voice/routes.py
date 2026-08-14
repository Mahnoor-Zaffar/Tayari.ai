"""Voice routes — real-time streaming transcription (Deepgram) + TTS bridge.

The TTS endpoints let the interview client speak each AI question aloud.
They go through the shared audio gateway so provider selection (OpenAI TTS,
mock fallback) and usage telemetry stay centralized.
"""

from __future__ import annotations

import asyncio
import json
import re

from fastapi import APIRouter, Depends, Response, WebSocket, WebSocketDisconnect

from ai.audio.deepgram_provider import DeepgramTranscriptionProvider as DeepgramProxy
from ai.audio.gateway import PROVIDER_MOCK, get_audio_gateway
from core.errors import RateLimitedError, ValidationError, success_response
from core.logging import get_logger
from core.rate_limit import InMemoryRateLimiter, RedisRateLimiter
from features.auth.dependencies import get_rate_limiter, get_token_service
from features.auth.guard import CurrentUser, get_current_user
from features.auth.jwt.service import TokenService
from features.auth.ws import verify_ws_token
from features.voice.schemas import TTSRequest

router = APIRouter(tags=["voice"])
log = get_logger("voice")


# ── TTS bridge ───────────────────────────────────────────────────────────────


def _audio_media_type(audio: bytes) -> str:
    """Detect the audio format from content so the browser plays it correctly.

    The mock provider emits a WAV; the real provider (OpenAI) returns MP3.
    Sniffing the bytes keeps the mapping independent of provider choice.
    """
    if audio[:4] == b"RIFF" and audio[8:12] == b"WAVE":
        return "audio/wav"
    return "audio/mpeg"


@router.get(
    "/voice/tts/status",
    summary="Check TTS availability",
    description="Report whether real speech synthesis (not the silent mock) is configured.",
)
async def tts_status(
    current_user: CurrentUser = Depends(get_current_user),
) -> dict:
    gateway = get_audio_gateway()
    provider = gateway.speech_provider_name
    return success_response({"available": provider != PROVIDER_MOCK, "provider": provider})


@router.post(
    "/voice/tts",
    summary="Synthesize speech",
    description="Convert text into audio (MP3 for OpenAI, WAV for the mock provider).",
    responses={
        200: {"content": {"audio/mpeg": {}, "audio/wav": {}}, "description": "Synthesized audio"},
    },
)
async def synthesize_speech(
    body: TTSRequest,
    current_user: CurrentUser = Depends(get_current_user),
    rate_limiter: RedisRateLimiter | InMemoryRateLimiter = Depends(get_rate_limiter),
) -> Response:
    if not await rate_limiter.check(
        f"tts:user:{current_user.id}",
        max_requests=TTS_RATE_MAX,
        window_seconds=TTS_RATE_WINDOW_SECONDS,
    ):
        raise RateLimitedError("Too many speech requests. Try again later.")

    text = _sanitize_text(body.text).strip()
    if not text:
        raise ValidationError("text must not be empty")

    gateway = get_audio_gateway()
    audio = await gateway.synthesize(
        text,
        voice=body.voice,
        session_id=body.session_id,
        interview_id=body.interview_id,
    )
    log.info(
        "TTS synthesized user=%s chars=%d sample_bytes=%d",
        current_user.id,
        len(text),
        len(audio),
    )
    return Response(content=audio, media_type=_audio_media_type(audio))


# ── Constants ─────────────────────────────────────────────────────────────────

MAX_TTS_TEXT_LENGTH = 5000
TTS_RATE_MAX = 30  # synthesized clips per window
TTS_RATE_WINDOW_SECONDS = 60

# ── Sanitization ─────────────────────────────────────────────────────────────

_INPUT_CLEAN_RE = re.compile(r"[\0-\x08\x0b\x0c\x0e-\x1f]")


def _sanitize_text(text: str) -> str:
    """Strip control characters so they cannot reach the TTS provider."""
    return _INPUT_CLEAN_RE.sub("", text)[:MAX_TTS_TEXT_LENGTH]


@router.websocket("/voice/stream")
async def voice_stream(
    websocket: WebSocket,
    token_service: TokenService = Depends(get_token_service),
) -> None:
    """Real-time speech-to-text via Deepgram streaming API.

    Protocol:
    1. Client connects
    2. Client sends JSON: {"type": "start", "language": "en", "token": "<access_token>"}
    3. Client sends binary audio chunks (PCM 16-bit mono 16kHz)
    4. Server sends JSON results:
       - {"type": "partial", "text": "..."}                          (interim)
       - {"type": "final", "text": "...", "speech_final": true/false} (finalized)
       - {"type": "error", "message": "..."}
    5. Client sends {"type": "stop"} or closes the WebSocket

    Security: the ``start`` message must include a valid access token; the
    connection is closed with 4401 otherwise.
    """
    await websocket.accept()
    log.info("Voice stream connected")

    deepgram: DeepgramProxy | None = None

    try:
        # ── Wait for start config ─────────────────────────────────────
        msg = await asyncio.wait_for(websocket.receive(), timeout=10.0)
        raw = msg.get("text", "")
        if not raw:
            await websocket.send_json({"type": "error", "message": "Expected start message"})
            await websocket.close()
            return

        config = json.loads(raw)
        if config.get("type") != "start":
            await websocket.send_json({"type": "error", "message": "Expected start message"})
            await websocket.close()
            return

        token = config.get("token", "")
        if await verify_ws_token(token_service, token) is None:
            await websocket.send_json({"type": "error", "message": "Unauthorized"})
            await websocket.close(code=4401)
            return

        language = config.get("language", "en")

        # ── Connect to Deepgram ───────────────────────────────────────
        deepgram = DeepgramProxy()
        await deepgram.connect(language=language)
        await websocket.send_json({"type": "started", "language": language})
        log.info("Voice stream started: language=%s", language)

        # ── Proxy audio + results concurrently ────────────────────────
        async def _forward_audio() -> None:
            """Read binary audio from browser and send to Deepgram."""
            try:
                while True:
                    message = await websocket.receive()

                    if message.get("type") == "websocket.disconnect":
                        break

                    if "text" in message:
                        try:
                            data = json.loads(message["text"])
                        except json.JSONDecodeError:
                            continue
                        if data.get("type") == "stop":
                            break
                    elif message.get("bytes"):
                        await deepgram.send_audio(message["bytes"])

                    # Notify client if Deepgram connection dropped silently
                    if deepgram.dropped:
                        try:
                            await websocket.send_json(
                                {
                                    "type": "error",
                                    "message": "Voice connection lost. Please restart microphone.",
                                }
                            )
                        except Exception:
                            pass
                        break
            except (WebSocketDisconnect, RuntimeError):
                log.info("Browser disconnected")
            except asyncio.CancelledError:
                pass

        async def _forward_results() -> None:
            """Read transcripts from Deepgram and send to browser."""
            try:
                async for event in deepgram.receive():
                    if event.type == "error":
                        # Terminal Deepgram failure — tell the browser so it can
                        # leave the recording state (it won't get any more data).
                        try:
                            await websocket.send_json(
                                {
                                    "type": "error",
                                    "message": "Voice connection lost. Please restart microphone.",
                                }
                            )
                        except (WebSocketDisconnect, RuntimeError):
                            pass
                        break
                    try:
                        if event.speech_final:
                            await websocket.send_json(
                                {
                                    "type": "final",
                                    "text": event.text,
                                    "speech_final": True,
                                }
                            )
                        elif event.is_final and event.text.strip():
                            await websocket.send_json(
                                {
                                    "type": "final",
                                    "text": event.text,
                                    "speech_final": False,
                                }
                            )
                        elif event.text.strip():
                            await websocket.send_json(
                                {
                                    "type": "partial",
                                    "text": event.text,
                                }
                            )
                    except (WebSocketDisconnect, RuntimeError):
                        break
            except asyncio.CancelledError:
                pass

        audio_task = asyncio.create_task(_forward_audio())
        result_task = asyncio.create_task(_forward_results())

        # Wait for either task to finish (client disconnect or Deepgram close)
        done, pending = await asyncio.wait(
            [audio_task, result_task],
            return_when=asyncio.FIRST_COMPLETED,
        )

        # Cancel remaining tasks
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    except TimeoutError:
        log.warning("Voice stream start timeout")
        try:
            await websocket.send_json({"type": "error", "message": "Start timeout"})
        except Exception:
            pass
    except json.JSONDecodeError:
        log.warning("Voice stream invalid JSON")
        try:
            await websocket.send_json({"type": "error", "message": "Invalid JSON"})
        except Exception:
            pass
    except Exception:
        log.exception("Voice stream error")
        try:
            await websocket.send_json({"type": "error", "message": "Internal error"})
        except Exception:
            pass
    finally:
        if deepgram:
            await deepgram.close()
        log.info("Voice stream closed")
