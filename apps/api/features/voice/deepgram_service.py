"""Compatibility shim — the Deepgram provider now lives in ``ai.audio``.

Kept so any lingering imports of ``features.voice.deepgram_service`` keep
working after the audio media-layer extraction.
"""

from ai.audio.deepgram_provider import DEEPGRAM_WS_URL, DeepgramTranscriptionProvider

DeepgramProxy = DeepgramTranscriptionProvider

__all__ = ["DeepgramProxy", "DeepgramTranscriptionProvider", "DEEPGRAM_WS_URL"]
