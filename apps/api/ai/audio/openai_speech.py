"""OpenAI text-to-speech provider."""

from __future__ import annotations

from typing import Any

from ai.audio.protocols import SpeechProvider
from core.config import settings


class OpenAISpeechProvider(SpeechProvider):
    """Synthesizes speech via the OpenAI TTS API (``/audio/speech``)."""

    def __init__(self, model: str = "", voice: str = "", client: Any | None = None) -> None:
        self._model = model or settings.TTS_MODEL
        self._voice = voice or settings.TTS_VOICE
        self._client = client  # AsyncOpenAI instance; injected for tests

    @property
    def model(self) -> str:
        return self._model

    @property
    def voice(self) -> str:
        return self._voice

    def _get_client(self) -> Any:
        if self._client is None:
            from openai import AsyncOpenAI

            self._client = AsyncOpenAI(
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_BASE_URL,
            )
        return self._client

    async def synthesize(self, text: str, voice: str | None = None) -> bytes:
        client = self._get_client()
        response = await client.audio.speech.create(
            model=self._model,
            voice=voice or self._voice,
            input=text,
        )
        return await response.read()
