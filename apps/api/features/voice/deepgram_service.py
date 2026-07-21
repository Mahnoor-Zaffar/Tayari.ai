"""Deepgram streaming proxy — forwards raw PCM audio to Deepgram and yields transcript events."""

from __future__ import annotations

import json
import urllib.parse
from collections.abc import AsyncIterator

import websockets
import websockets.asyncio.client

from core.config import settings
from core.logging import get_logger

log = get_logger("voice.deepgram")

DEEPGRAM_WS_URL = "wss://api.deepgram.com/v1/listen"


class DeepgramProxy:
    """Maintains a WebSocket connection to Deepgram's streaming API."""

    def __init__(self) -> None:
        self._ws: websockets.asyncio.client.ClientConnection | None = None
        self._connected = False

    async def connect(self, language: str = "en") -> None:
        if not settings.DEEPGRAM_API_KEY:
            raise RuntimeError("DEEPGRAM_API_KEY is not configured")

        params = {
            "model": settings.DEEPGRAM_MODEL,
            "encoding": "linear16",
            "sample_rate": "16000",
            "channels": "1",
            "interim_results": "true",
            "endpointing": str(settings.DEEPGRAM_ENDPOINTING),
            "smart_format": "true",
            "language": language,
            "utterance_end_ms": "1000",
            "vad_events": "true",
        }

        url = f"{DEEPGRAM_WS_URL}?{urllib.parse.urlencode(params)}"
        headers = {"Authorization": f"Token {settings.DEEPGRAM_API_KEY}"}

        log.info("Connecting to Deepgram: language=%s, model=%s", language, settings.DEEPGRAM_MODEL)

        self._ws = await websockets.asyncio.client.connect(
            url,
            additional_headers=headers,
            max_size=None,  # no limit on incoming JSON
        )
        self._connected = True
        log.info("Deepgram connected")

    async def send_audio(self, data: bytes) -> None:
        if self._ws and self._connected:
            await self._ws.send(data)

    async def receive(self) -> AsyncIterator[dict]:
        """Yield transcript events from Deepgram."""
        if not self._ws:
            return

        try:
            async for raw in self._ws:
                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    continue

                msg_type = msg.get("type")

                if msg_type == "Results":
                    channel = msg.get("channel", {})
                    alternatives = channel.get("alternatives", [])
                    if not alternatives:
                        continue

                    transcript = alternatives[0].get("transcript", "")
                    if not transcript.strip():
                        continue

                    is_final = msg.get("is_final", False)
                    speech_final = msg.get("speech_final", False)

                    yield {
                        "transcript": transcript,
                        "is_final": is_final,
                        "speech_final": speech_final,
                    }

                elif msg_type == "UtteranceEnd":
                    # Deepgram detected end of an utterance
                    yield {
                        "transcript": "",
                        "is_final": True,
                        "speech_final": True,
                    }

                elif msg_type == "Metadata":
                    log.debug("Deepgram metadata: %s", msg.get("duration", 0))

        except websockets.ConnectionClosed as exc:
            log.warning("Deepgram connection closed: %s", exc)
        except Exception:
            log.exception("Deepgram receive error")
        finally:
            self._connected = False

    async def close(self) -> None:
        if self._ws and self._connected:
            try:
                await self._ws.close()
            except Exception:
                pass
            self._connected = False
            log.info("Deepgram connection closed")
