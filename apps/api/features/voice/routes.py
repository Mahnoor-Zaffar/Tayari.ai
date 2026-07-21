"""Voice routes — real-time streaming transcription via Deepgram."""

from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from core.logging import get_logger

from .deepgram_service import DeepgramProxy

router = APIRouter(tags=["voice"])
log = get_logger("voice")


@router.websocket("/voice/stream")
async def voice_stream(websocket: WebSocket) -> None:
    """Real-time speech-to-text via Deepgram streaming API.

    Protocol:
    1. Client connects
    2. Client sends JSON: {"type": "start", "language": "en"}
    3. Client sends binary audio chunks (PCM 16-bit mono 16kHz)
    4. Server sends JSON results:
       - {"type": "partial", "text": "..."}                          (interim)
       - {"type": "final", "text": "...", "speech_final": true/false} (finalized)
       - {"type": "error", "message": "..."}
    5. Client sends {"type": "stop"} or closes the WebSocket
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

                    if message.get("text"):
                        data = json.loads(message["text"])
                        if data.get("type") == "stop":
                            break
                    elif message.get("bytes"):
                        await deepgram.send_audio(message["bytes"])
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
                            # End of utterance — auto-submit signal
                            await websocket.send_json(
                                {
                                    "type": "final",
                                    "text": event["transcript"],
                                    "speech_final": True,
                                }
                            )
                        elif event["is_final"]:
                            # Confirmed text but not end of utterance
                            await websocket.send_json(
                                {
                                    "type": "final",
                                    "text": event["transcript"],
                                    "speech_final": False,
                                }
                            )
                        else:
                            # Interim result
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
