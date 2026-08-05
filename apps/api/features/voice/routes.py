"""Voice routes — real-time streaming transcription via Deepgram."""

from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from core.logging import get_logger
from features.auth.dependencies import get_token_service
from features.auth.jwt.service import TokenService
from features.auth.ws import verify_ws_token

from .deepgram_service import DeepgramProxy

router = APIRouter(tags=["voice"])
log = get_logger("voice")


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
        async def _forward_audio():
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

        async def _forward_results():
            """Read transcripts from Deepgram and send to browser."""
            try:
                async for event in deepgram.receive():
                    try:
                        if event["speech_final"]:
                            await websocket.send_json(
                                {
                                    "type": "final",
                                    "text": event["transcript"],
                                    "speech_final": True,
                                }
                            )
                        elif event["is_final"] and event["transcript"].strip():
                            await websocket.send_json(
                                {
                                    "type": "final",
                                    "text": event["transcript"],
                                    "speech_final": False,
                                }
                            )
                        elif event["transcript"].strip():
                            await websocket.send_json(
                                {
                                    "type": "partial",
                                    "text": event["transcript"],
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
