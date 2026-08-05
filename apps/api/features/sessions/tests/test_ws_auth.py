"""Tests for WebSocket authentication + session ownership.

Covers the security contract of ``/sessions/{id}/ws``:
- the first message must be an authenticated ``session.join``
- invalid / missing tokens are rejected with 4401
- a valid token for a non-owner is rejected with 4403
- the session owner gets a ``session.connected`` ack
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from features.auth.dependencies import get_token_service
from features.auth.exceptions import InvalidTokenError
from features.sessions.dependencies import get_session_service
from features.sessions.service import SessionService

OWNER_ID = "11111111-1111-1111-1111-111111111111"
OTHER_ID = "22222222-2222-2222-2222-222222222222"
SESSION_ID = "33333333-3333-3333-3333-333333333333"

VALID_TOKEN = "valid-access-token"


class FakeTokenService:
    """Minimal stand-in for TokenService: only the verify() path used by WS."""

    def __init__(self, valid_sub: str = OWNER_ID) -> None:
        self._valid_sub = valid_sub

    async def verify(self, token: str, expected_type: str) -> SimpleNamespace:
        if token != VALID_TOKEN:
            raise InvalidTokenError("bad token")
        return SimpleNamespace(sub=self._valid_sub)


def _make_mock_service(user_id: str = OWNER_ID) -> AsyncMock:
    mock = AsyncMock(spec=SessionService)
    mock.get_session.return_value = {
        "session_id": SESSION_ID,
        "interview_id": "44444444-4444-4444-4444-444444444444",
        "user_id": user_id,
        "state": "active",
        "remaining_seconds": 1800,
        "current_question": None,
        "current_question_type": "initial",
    }
    return mock


@pytest.fixture
def app_ctx():
    from main import app

    mock_service = _make_mock_service()
    token_service = FakeTokenService()
    app.dependency_overrides[get_session_service] = lambda: mock_service
    app.dependency_overrides[get_token_service] = lambda: token_service

    yield app

    app.dependency_overrides.clear()


def _ws_url() -> str:
    return f"/api/v1/sessions/{SESSION_ID}/ws"


def _receive_close_code(ws) -> int:
    """Drain frames until the server-initiated close frame and return its code."""
    for _ in range(4):
        frame = ws.receive()
        if frame["type"] == "websocket.close":
            return frame["code"]
        assert frame["type"] == "websocket.send"
    raise AssertionError("Server did not close the WebSocket")


def test_ws_requires_join_first(app_ctx):
    with TestClient(app_ctx) as client:
        with client.websocket_connect(_ws_url()) as ws:
            ws.send_json({"type": "user.answer", "payload": {"text": "hello"}})
            assert _receive_close_code(ws) == 4401


def test_ws_rejects_missing_token(app_ctx):
    with TestClient(app_ctx) as client:
        with client.websocket_connect(_ws_url()) as ws:
            ws.send_json({"type": "session.join", "payload": {}})
            assert _receive_close_code(ws) == 4401


def test_ws_rejects_invalid_token(app_ctx):
    with TestClient(app_ctx) as client:
        with client.websocket_connect(_ws_url()) as ws:
            ws.send_json({"type": "session.join", "payload": {"token": "garbage-token"}})
            assert _receive_close_code(ws) == 4401


def test_ws_rejects_non_owner(app_ctx):
    app_ctx.dependency_overrides[get_token_service] = lambda: FakeTokenService(valid_sub=OTHER_ID)
    with TestClient(app_ctx) as client:
        with client.websocket_connect(_ws_url()) as ws:
            ws.send_json({"type": "session.join", "payload": {"token": VALID_TOKEN}})
            assert _receive_close_code(ws) == 4403


def test_ws_accepts_session_owner(app_ctx):
    with TestClient(app_ctx) as client:
        with client.websocket_connect(_ws_url()) as ws:
            ws.send_json({"type": "session.join", "payload": {"token": VALID_TOKEN}})
            data = ws.receive_json()
    assert data["type"] == "session.connected"
    assert data["payload"]["session_id"] == SESSION_ID
