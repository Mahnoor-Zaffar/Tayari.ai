"""Tests for the voice TTS bridge endpoints.

Covers authentication, provider status reporting (mock vs OpenAI), audio
content, and per-user rate limiting on synthesis.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from core.rate_limit import InMemoryRateLimiter
from features.auth.dependencies import get_rate_limiter
from features.auth.guard import CurrentUser, get_current_user

USER_ID = "00000000-0000-0000-0000-000000000001"


def _make_user() -> CurrentUser:
    return CurrentUser(
        id=USER_ID,
        email="test@test.com",
        username="testuser",
        display_name="Test User",
        email_verified=True,
        is_active=True,
        roles=["user"],
        permissions=["interview:read", "interview:write"],
    )


class _DenyLimiter:
    async def check(self, *args, **kwargs) -> bool:
        return False


@pytest.fixture
def app_ctx():
    import ai.audio.gateway as gateway_module
    from main import app

    gateway_module._audio_gateway = None
    app.dependency_overrides[get_current_user] = lambda: _make_user()
    app.dependency_overrides[get_rate_limiter] = lambda: InMemoryRateLimiter()
    yield app
    app.dependency_overrides.clear()


def test_tts_status_requires_auth(app_ctx):
    app_ctx.dependency_overrides.pop(get_current_user, None)
    with TestClient(app_ctx) as client:
        response = client.get("/api/v1/voice/tts/status")
    assert response.status_code == 401


def test_tts_status_reports_unavailable_for_mock(app_ctx, monkeypatch):
    monkeypatch.setattr("core.config.settings.OPENAI_API_KEY", "")
    monkeypatch.setattr("core.config.settings.TTS_PROVIDER", "openai")
    with TestClient(app_ctx) as client:
        response = client.get("/api/v1/voice/tts/status")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["available"] is False
    assert data["provider"] == "mock"


def test_tts_status_reports_available_for_openai(app_ctx, monkeypatch):
    monkeypatch.setattr("core.config.settings.OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr("core.config.settings.TTS_PROVIDER", "openai")
    with TestClient(app_ctx) as client:
        response = client.get("/api/v1/voice/tts/status")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["available"] is True
    assert data["provider"] == "openai"


def test_tts_synthesize_requires_auth(app_ctx):
    app_ctx.dependency_overrides.pop(get_current_user, None)
    with TestClient(app_ctx) as client:
        response = client.post("/api/v1/voice/tts", json={"text": "Hello"})
    assert response.status_code == 401


def test_tts_synthesize_returns_wav_with_mock(app_ctx, monkeypatch):
    monkeypatch.setattr("core.config.settings.OPENAI_API_KEY", "")
    with TestClient(app_ctx) as client:
        response = client.post(
            "/api/v1/voice/tts",
            json={"text": "Tell me about yourself", "session_id": "s1", "interview_id": "i1"},
        )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("audio/wav")
    assert response.content.startswith(b"RIFF")


def test_tts_synthesize_rejects_blank_text(app_ctx):
    with TestClient(app_ctx) as client:
        response = client.post("/api/v1/voice/tts", json={"text": "   "})
    assert response.status_code == 422


def test_tts_synthesize_rate_limits_per_user(app_ctx, monkeypatch):
    monkeypatch.setattr("core.config.settings.OPENAI_API_KEY", "")
    app_ctx.dependency_overrides[get_rate_limiter] = lambda: _DenyLimiter()
    with TestClient(app_ctx) as client:
        response = client.post("/api/v1/voice/tts", json={"text": "Hello"})
    assert response.status_code == 429
