"""Audio media layer — provider-agnostic speech protocols.

Split into two small protocols so STT, TTS and (later) translation stay
independent capabilities behind the same calling convention the model
gateway uses for text models.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass


@dataclass(slots=True)
class TranscriptionEvent:
    """A single transcript event yielded by a ``TranscriptionProvider``."""

    type: str  # "partial" | "final" | "utterance_end" | "error"
    text: str = ""
    is_final: bool = False
    speech_final: bool = False
    error: str | None = None


class TranscriptionProvider(ABC):
    """Speech-to-text over a streaming audio transport.

    ``send_audio`` feeds raw PCM one-way into the provider; ``receive``
    yields finalized/interim transcript events. ``connect`` must be called
    before ``send_audio``/``receive``, ``close`` afterwards.
    """

    @abstractmethod
    async def connect(self, language: str = "en") -> None: ...

    @abstractmethod
    async def send_audio(self, data: bytes) -> None: ...

    @abstractmethod
    def receive(self) -> AsyncIterator[TranscriptionEvent]: ...

    @abstractmethod
    async def close(self) -> None: ...

    @property
    @abstractmethod
    def dropped(self) -> bool: ...


class SpeechProvider(ABC):
    """Text-to-speech. ``synthesize`` returns encoded audio bytes (MP3 by default)."""

    @abstractmethod
    async def synthesize(self, text: str, voice: str | None = None) -> bytes: ...

    @property
    @abstractmethod
    def model(self) -> str: ...
