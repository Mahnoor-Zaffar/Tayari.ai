"""Mock text-to-speech for offline/local dev and CI.

Emits a valid silent WAV so the audio path is exercisable end-to-end without
an API key — the same degree of parity ``MockProvider`` gives the LLM gateway.
"""

from __future__ import annotations

import io
import wave

from ai.audio.protocols import SpeechProvider

SAMPLE_RATE = 16000
SAMPLE_WIDTH_BYTES = 2
CHANNELS = 1


def _silent_wav(seconds: float = 0.5) -> bytes:
    """Return a minimal, valid PCM WAV of pure silence."""
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(CHANNELS)
        wav.setsampwidth(SAMPLE_WIDTH_BYTES)
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes(b"\x00\x00" * int(SAMPLE_RATE * seconds))
    return buffer.getvalue()


class MockSpeechProvider(SpeechProvider):
    """Always returns a silent WAV and remembers the requested text."""

    def __init__(self, model: str = "mock-tts") -> None:
        self._model = model
        self._last_text: str | None = None

    @property
    def model(self) -> str:
        return self._model

    @property
    def last_text(self) -> str | None:
        return self._last_text

    async def synthesize(self, text: str, voice: str | None = None) -> bytes:
        self._last_text = text
        return _silent_wav(0.5)
