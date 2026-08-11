"""Audio media layer — provider-agnostic speech interfaces (STT, TTS).

Structured as two small protocols (``TranscriptionProvider``, ``SpeechProvider``)
so transcription, speech generation and (later) translation stay independent
capabilities behind the same calling convention used by the model gateway.
"""

from ai.audio.gateway import AudioGateway, get_audio_gateway
from ai.audio.protocols import SpeechProvider, TranscriptionEvent, TranscriptionProvider

__all__ = [
    "AudioGateway",
    "get_audio_gateway",
    "SpeechProvider",
    "TranscriptionEvent",
    "TranscriptionProvider",
]
