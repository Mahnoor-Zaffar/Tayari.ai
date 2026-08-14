"""Deepgram streaming transcription provider (STT)."""

from __future__ import annotations

import json
import urllib.parse
from collections.abc import AsyncIterator

import websockets
import websockets.asyncio.client

from ai.audio.protocols import TranscriptionEvent, TranscriptionProvider
from core.config import settings
from core.logging import get_logger

log = get_logger("ai.audio.deepgram")

DEEPGRAM_WS_URL = "wss://api.deepgram.com/v1/listen"


class DeepgramTranscriptionProvider(TranscriptionProvider):
    """Streaming speech-to-text via Deepgram's listen WebSocket API.

    Raw PCM audio (16-bit mono 16 kHz) is forwarded to Deepgram and interim /
    final transcript events are yielded back to the caller. The wire protocol
    is deliberately preserved from the previous ``DeepgramProxy`` so existing
    consumers and tests keep working.
    """

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or settings.DEEPGRAM_API_KEY
        self._ws: websockets.asyncio.client.ClientConnection | None = None
        self._connected = False
        self._dropped = False
        self._language = "en"

    @property
    def language(self) -> str:
        return self._language

    async def connect(self, language: str = "en") -> None:
        if not self._api_key:
            raise RuntimeError("DEEPGRAM_API_KEY is not configured")

        self._language = language

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
        headers = {"Authorization": f"Token {self._api_key}"}

        log.info("Connecting to Deepgram: language=%s, model=%s", language, settings.DEEPGRAM_MODEL)

        self._ws = await websockets.asyncio.client.connect(
            url,
            additional_headers=headers,
            max_size=None,  # no limit on incoming JSON
        )
        self._connected = True
        log.info("Deepgram connected")

    async def send_audio(self, data: bytes) -> None:
        if not self._ws or not self._connected:
            self._dropped = True
            return
        try:
            await self._ws.send(data)
        except websockets.ConnectionClosed:
            self._connected = False
            self._dropped = True
            log.warning("Deepgram connection dropped during send")

    async def receive(self) -> AsyncIterator[TranscriptionEvent]:
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

                    is_final = bool(msg.get("is_final", False))
                    speech_final = bool(msg.get("speech_final", False))

                    yield TranscriptionEvent(
                        type="final" if (is_final or speech_final) else "partial",
                        text=transcript,
                        is_final=is_final,
                        speech_final=speech_final,
                    )

                elif msg_type == "UtteranceEnd":
                    # Deepgram detected end of an utterance
                    yield TranscriptionEvent(
                        type="utterance_end",
                        text="",
                        is_final=True,
                        speech_final=True,
                    )

                elif msg_type == "Metadata":
                    log.debug("Deepgram metadata: %s", msg.get("duration", 0))

        except websockets.ConnectionClosed as exc:
            self._connected = False
            self._dropped = True
            log.warning("Deepgram connection closed: %s", exc)
            yield TranscriptionEvent(type="error", error=f"Deepgram connection closed: {exc}")
        except Exception as exc:
            self._connected = False
            self._dropped = True
            log.exception("Deepgram receive error")
            yield TranscriptionEvent(type="error", error=f"Deepgram receive error: {exc}")
        finally:
            self._connected = False

    async def close(self) -> None:
        if self._ws and self._connected:
            try:
                await self._ws.close()
            except Exception as exc:
                log.warning("Deepgram close failed: %s", exc)
            self._connected = False
            log.info("Deepgram connection closed")

    @property
    def dropped(self) -> bool:
        return self._dropped
