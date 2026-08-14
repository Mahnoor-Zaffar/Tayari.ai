"""Tests for the audio media layer (STT/TTS providers + audio gateway)."""

from __future__ import annotations

import io
import wave

import pytest

from ai.audio.deepgram_provider import DeepgramTranscriptionProvider
from ai.audio.gateway import PROVIDER_MOCK, AudioGateway
from ai.audio.mock_speech import MockSpeechProvider, _silent_wav
from ai.audio.openai_speech import OpenAISpeechProvider


def test_silent_wav_is_valid_pcm() -> None:
    audio = _silent_wav(0.25)
    with wave.open(io.BytesIO(audio), "rb") as wav:
        assert wav.getframerate() == 16000
        assert wav.getnchannels() == 1
        assert wav.getsampwidth() == 2
        assert wav.getnframes() > 0


class _FakeRecorder:
    def __init__(self) -> None:
        self.records = []

    def record_sync(self, record) -> None:
        self.records.append(record)


@pytest.mark.asyncio
async def test_mock_speech_provider_returns_wav() -> None:
    provider = MockSpeechProvider()
    audio = await provider.synthesize("Hello")
    assert audio.startswith(b"RIFF")
    assert provider.last_text == "Hello"


@pytest.mark.asyncio
async def test_gateway_uses_mock_when_key_absent(monkeypatch) -> None:
    monkeypatch.setattr("core.config.settings.OPENAI_API_KEY", "")
    monkeypatch.setattr("core.config.settings.TTS_PROVIDER", "openai")
    gateway = AudioGateway(recorder=_FakeRecorder())
    assert isinstance(gateway.speech_provider(), MockSpeechProvider)
    assert gateway.speech_provider_name == PROVIDER_MOCK


@pytest.mark.asyncio
async def test_gateway_synthesize_records_usage(monkeypatch) -> None:
    monkeypatch.setattr("core.config.settings.OPENAI_API_KEY", "")
    recorder = _FakeRecorder()
    gateway = AudioGateway(recorder=recorder)
    audio = await gateway.synthesize("What is Redis?", session_id="s1", interview_id="i1")
    assert audio.startswith(b"RIFF")
    assert len(recorder.records) == 1
    rec = recorder.records[0]
    assert rec.task == "tts"
    assert rec.session_id == "s1"
    assert rec.interview_id == "i1"
    assert rec.is_error is False


@pytest.mark.asyncio
async def test_gateway_records_error_when_tts_fails() -> None:
    recorder = _FakeRecorder()
    gateway = AudioGateway(recorder=recorder)

    class BoomProvider(MockSpeechProvider):
        async def synthesize(self, text: str, voice: str | None = None) -> bytes:
            raise RuntimeError("tts down")

    gateway._tts = BoomProvider()
    with pytest.raises(RuntimeError):
        await gateway.synthesize("boom")
    assert len(recorder.records) == 1
    assert recorder.records[0].is_error is True
    assert "tts down" in (recorder.records[0].error_message or "")


@pytest.mark.asyncio
async def test_gateway_synthesize_uses_openai_when_key_present(monkeypatch) -> None:
    monkeypatch.setattr("core.config.settings.OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr("core.config.settings.TTS_PROVIDER", "openai")
    gateway = AudioGateway(recorder=_FakeRecorder())
    assert isinstance(gateway.speech_provider(), OpenAISpeechProvider)


def test_openai_speech_config_defaults(monkeypatch) -> None:
    monkeypatch.setattr("core.config.settings.TTS_MODEL", "tts-1-hd")
    monkeypatch.setattr("core.config.settings.TTS_VOICE", "shimmer")
    provider = OpenAISpeechProvider()
    assert provider.model == "tts-1-hd"
    assert provider.voice == "shimmer"


@pytest.mark.asyncio
async def test_deepgram_provider_requires_api_key(monkeypatch) -> None:
    monkeypatch.setattr("core.config.settings.DEEPGRAM_API_KEY", "")
    provider = DeepgramTranscriptionProvider()
    with pytest.raises(RuntimeError, match="DEEPGRAM_API_KEY"):
        await provider.connect(language="en")
