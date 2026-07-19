"""Voice streaming service with FunASR + Whisper fallback.

When FunASR is available: true streaming transcription.
When not available: accumulates audio and batch-transcribes via Whisper every 2s.
Either way, the frontend gets the same WebSocket protocol.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass

logger = logging.getLogger("voice.streaming")

# ── Try loading FunASR ──────────────────────────────────────────────────────

_funasr_model = None
_funasr_available = False


def _try_load_funasr():
    global _funasr_model, _funasr_available
    if _funasr_available:
        return
    try:
        from funasr import AutoModel

        _funasr_model = AutoModel(
            model="paraformer-zh-streaming",
            vad_model="fsmn-vad",
            punc_model="ct-punc-c",
        )
        _funasr_available = True
        logger.info("FunASR model loaded successfully")
    except Exception:
        _funasr_available = False
        logger.info("FunASR not available — using Whisper fallback")


# ── Whisper fallback (batch via OpenRouter) ──────────────────────────────────


async def _whisper_transcribe(audio_bytes: bytes, language: str = "en") -> str:
    """Transcribe audio using the existing Whisper endpoint."""
    from .whisper import TranscriptionError, transcribe_audio

    try:
        result = await transcribe_audio(
            audio_bytes,
            filename="stream-chunk.webm",
            language=language,
        )
        return result.get("text", "")
    except TranscriptionError as exc:
        logger.warning("Whisper fallback failed: %s", exc)
    except Exception as exc:
        logger.warning("Whisper fallback failed: %s", exc)
    return ""


# ── Transcript result ────────────────────────────────────────────────────────


@dataclass
class TranscriptResult:
    text: str
    is_final: bool
    language: str = "en"
    timestamp_ms: int = 0
    error_message: str | None = None


# ── Streaming session ────────────────────────────────────────────────────────


class StreamingSession:
    """Manages a single streaming transcription session.

    If FunASR is available, each audio chunk is processed immediately.
    Otherwise, audio is accumulated and batch-transcribed via Whisper every 2s.
    """

    BATCH_INTERVAL_S = 2.0

    def __init__(self, language: str = "en"):
        self.language = language
        self._queue: asyncio.Queue[TranscriptResult | None] = asyncio.Queue()
        self._closed = False
        self._audio_buffer = bytearray()
        self._batch_task: asyncio.Task | None = None

    async def start(self) -> None:
        """Start the batch processor if needed."""
        if not _funasr_available:
            _try_load_funasr()

        if not _funasr_available:
            self._batch_task = asyncio.create_task(self._batch_processor())

    async def feed_audio(self, audio_bytes: bytes) -> None:
        """Feed raw audio bytes."""
        if self._closed:
            return

        if _funasr_available and _funasr_model is not None:
            # True streaming with FunASR
            try:
                result = _funasr_model.generate(input=audio_bytes)
                text = ""
                if result and isinstance(result, list):
                    for item in result:
                        if isinstance(item, dict) and "text" in item:
                            text = item["text"]
                            break
                if text.strip():
                    await self._queue.put(
                        TranscriptResult(
                            text=text.strip(),
                            is_final=True,
                            language=self.language,
                            timestamp_ms=int(time.time() * 1000),
                        )
                    )
            except Exception:
                logger.exception("FunASR transcription failed")
        else:
            # Accumulate for batch Whisper
            self._audio_buffer.extend(audio_bytes)

    async def _batch_processor(self) -> None:
        """Periodically send accumulated audio to Whisper."""
        consecutive_failures = 0
        while not self._closed:
            await asyncio.sleep(self.BATCH_INTERVAL_S)
            if self._closed:
                break

            if len(self._audio_buffer) < 1600:  # Need at least ~100ms of audio
                continue

            audio_chunk = bytes(self._audio_buffer)
            self._audio_buffer.clear()

            try:
                text = await _whisper_transcribe(audio_chunk, self.language)
                if text.strip():
                    consecutive_failures = 0
                    await self._queue.put(
                        TranscriptResult(
                            text=text.strip(),
                            is_final=True,
                            language=self.language,
                            timestamp_ms=int(time.time() * 1000),
                        )
                    )
                else:
                    consecutive_failures += 1
            except Exception:
                consecutive_failures += 1
                logger.exception("Whisper batch transcription failed")

            # After 3 consecutive failures, notify the client
            if consecutive_failures == 3:
                await self._queue.put(
                    TranscriptResult(
                        text="",
                        is_final=True,
                        language=self.language,
                        timestamp_ms=0,
                        error_message="Transcription failed. Check that OPENAI_API_KEY is valid.",
                    )
                )

    async def results(self) -> AsyncIterator[TranscriptResult]:
        """Yield transcript results."""
        while True:
            item = await self._queue.get()
            if item is None:
                break
            yield item

    async def close(self) -> None:
        """Flush remaining audio and close."""
        self._closed = True

        # Flush any remaining audio
        if self._audio_buffer and len(self._audio_buffer) >= 1600:
            try:
                text = await _whisper_transcribe(bytes(self._audio_buffer), self.language)
                if text.strip():
                    await self._queue.put(
                        TranscriptResult(
                            text=text.strip(),
                            is_final=True,
                            language=self.language,
                            timestamp_ms=int(time.time() * 1000),
                        )
                    )
            except Exception:
                pass
            self._audio_buffer.clear()

        if self._batch_task and not self._batch_task.done():
            self._batch_task.cancel()
            try:
                await self._batch_task
            except asyncio.CancelledError:
                pass

        await self._queue.put(None)
