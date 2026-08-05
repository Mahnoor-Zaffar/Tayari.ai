"""Tests for voice stream WebSocket authentication."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from features.auth.dependencies import get_token_service
from features.auth.exceptions import InvalidTokenError

VALID_TOKEN = "valid-access-token"


class FakeTokenService:
    async def verify(self, token: str, expected_type: str) -> SimpleNamespace:
        if token != VALID_TOKEN:
            raise InvalidTokenError("bad token")
        return SimpleNamespace(sub="11111111-1111-1111-1111-111111111111")


@pytest.fixture
def app_ctx():
    from main import app

    app.dependency_overrides[get_token_service] = lambda: FakeTokenService()
    yield app
    app.dependency_overrides.clear()


def _receive_close_code(ws) -> int:
    for _ in range(4):
        frame = ws.receive()
        if frame["type"] == "websocket.close":
            return frame["code"]
        assert frame["type"] == "websocket.send"
    raise AssertionError("Server did not close the WebSocket")


def test_voice_stream_rejects_missing_token(app_ctx):
    with TestClient(app_ctx) as client:
        with client.websocket_connect("/api/v1/voice/stream") as ws:
            ws.send_json({"type": "start", "language": "en"})
            assert _receive_close_code(ws) == 4401


def test_voice_stream_rejects_invalid_token(app_ctx):
    with TestClient(app_ctx) as client:
        with client.websocket_connect("/api/v1/voice/stream") as ws:
            ws.send_json({"type": "start", "language": "en", "token": "garbage"})
            assert _receive_close_code(ws) == 4401


def test_voice_stream_accepts_valid_token(app_ctx):
    with patch("features.voice.routes.DeepgramProxy") as mock_proxy:
        instance = AsyncMock()
        instance.dropped = False
        instance.connect = AsyncMock()
        instance.close = AsyncMock()
        instance.receive = AsyncMock()
        instance.receive.__aiter__ = AsyncMock(return_value=iter([]))
        mock_proxy.return_value = instance

        with TestClient(app_ctx) as client:
            with client.websocket_connect("/api/v1/voice/stream") as ws:
                ws.send_json({"type": "start", "language": "en", "token": VALID_TOKEN})
                data = ws.receive_json()
                ws.send_json({"type": "stop"})

    assert data["type"] == "started"
    assert data["language"] == "en"
    instance.connect.assert_awaited_once_with(language="en")
