"""Audio gateway — single entry point for STT/TTS, mirroring the model gateway.

Picks the configured STT / TTS providers (falling back to mocks when no API
key is present) so voice features keep working offline and in CI, and records
every synthesis / transcription into the shared ``ai_usage`` telemetry.
"""

from __future__ import annotations

import logging
import time

from ai.audio.deepgram_provider import DeepgramTranscriptionProvider
from ai.audio.mock_speech import MockSpeechProvider
from ai.audio.openai_speech import OpenAISpeechProvider
from ai.audio.protocols import SpeechProvider, TranscriptionEvent, TranscriptionProvider
from ai.usage.recorder import UsageRecord, UsageRecorder, get_usage_recorder
from core.config import settings

logger = logging.getLogger(__name__)

TASK_STT = "stt"
TASK_TTS = "tts"

PROVIDER_OPENAI = "openai"
PROVIDER_MOCK = "mock"
PROVIDER_DEEPGRAM = "deepgram"


class AudioGateway:
    """Routes STT/TTS calls to the configured providers and records usage."""

    def __init__(self, recorder: UsageRecorder | None = None) -> None:
        self._recorder = recorder
        self._stt: TranscriptionProvider | None = None
        self._tts: SpeechProvider | None = None

    # ── provider selection ────────────────────────────────────────────────

    def transcription_provider(self) -> TranscriptionProvider:
        """Return the STT provider (Deepgram when configured, else raise)."""
        if self._stt is None:
            if settings.STT_PROVIDER != PROVIDER_DEEPGRAM:
                logger.warning("Unsupported STT_PROVIDER=%r — falling back to deepgram", settings.STT_PROVIDER)
            self._stt = DeepgramTranscriptionProvider()
        return self._stt

    def speech_provider(self) -> SpeechProvider:
        """Return the TTS provider (OpenAI when a key is set, else mock)."""
        if self._tts is None:
            if settings.TTS_PROVIDER == PROVIDER_OPENAI and settings.OPENAI_API_KEY:
                self._tts = OpenAISpeechProvider()
            else:
                if settings.TTS_PROVIDER == PROVIDER_OPENAI:
                    logger.warning("No OPENAI_API_KEY set — using MockSpeechProvider for TTS")
                self._tts = MockSpeechProvider()
        return self._tts

    @property
    def speech_provider_name(self) -> str:
        return PROVIDER_OPENAI if isinstance(self.speech_provider(), OpenAISpeechProvider) else PROVIDER_MOCK

    # ── TTS ───────────────────────────────────────────────────────────────

    async def synthesize(
        self,
        text: str,
        *,
        voice: str | None = None,
        session_id: str | None = None,
        interview_id: str | None = None,
    ) -> bytes:
        """Synthesize speech, recording a ``tts`` usage row on success/failure."""
        provider = self.speech_provider()
        started = time.monotonic()
        try:
            audio = await provider.synthesize(text, voice=voice)
        except Exception as exc:
            self._record(
                TASK_TTS,
                provider.model,
                latency_ms=(time.monotonic() - started) * 1000,
                is_error=True,
                error_message=str(exc),
                session_id=session_id,
                interview_id=interview_id,
            )
            raise
        self._record(
            TASK_TTS,
            provider.model,
            latency_ms=(time.monotonic() - started) * 1000,
            session_id=session_id,
            interview_id=interview_id,
        )
        return audio

    # ── STT telemetry ─────────────────────────────────────────────────────

    def record_stt_event(
        self,
        *,
        language: str,
        is_error: bool = False,
        error_message: str | None = None,
        session_id: str | None = None,
        interview_id: str | None = None,
    ) -> None:
        """Record a ``stt`` usage row (Deepgram is metered outside the gateway)."""
        self._record(
            TASK_STT,
            settings.DEEPGRAM_MODEL,
            latency_ms=0.0,
            is_error=is_error,
            error_message=error_message,
            session_id=session_id,
            interview_id=interview_id,
        )

    # ── recording helpers ─────────────────────────────────────────────────

    def _record(
        self,
        task: str,
        model: str,
        *,
        latency_ms: float,
        is_error: bool = False,
        error_message: str | None = None,
        session_id: str | None = None,
        interview_id: str | None = None,
    ) -> None:
        recorder = self._recorder or get_usage_recorder()
        recorder.record_sync(
            UsageRecord(
                task=task,
                provider=self.speech_provider_name if task == TASK_TTS else PROVIDER_DEEPGRAM,
                model=model,
                latency_ms=round(latency_ms, 1),
                is_error=is_error,
                error_message=error_message,
                interview_id=interview_id,
                session_id=session_id,
                estimated_cost_cents=0.0,
            )
        )


_audio_gateway: AudioGateway | None = None


def get_audio_gateway() -> AudioGateway:
    """Return the shared audio gateway singleton."""
    global _audio_gateway
    if _audio_gateway is None:
        _audio_gateway = AudioGateway()
    return _audio_gateway


__all__ = [
    "AudioGateway",
    "get_audio_gateway",
    "TranscriptionEvent",
]
