"""Integration tests for the sessions feature.

Tests the full lifecycle: REST API → Session Manager → Persistence.
Uses mocked auth and mocked service for isolated endpoint testing.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from main import app

# ── Mock the session service dependency ──────────────────────────────────────


@pytest.fixture(autouse=True)
def _mock_session_service():
    """Replace the session service dependency with a mock for all tests."""
    mock_service = AsyncMock()

    mock_service.start_session.return_value = {
        "session_id": "test-session-uuid",
        "interview_id": "test-interview-uuid",
        "status": "active",
        "initial_question": "Welcome! Tell me about yourself.",
    }
    mock_service.get_status.return_value = {
        "session_id": "test-session-uuid",
        "interview_id": "test-interview-uuid",
        "user_id": "test-user-uuid",
        "state": "active",
        "elapsed_seconds": 0,
        "remaining_seconds": 1800,
        "total_paused_seconds": 0,
        "disconnect_count": 0,
        "error_count": 0,
    }
    mock_service.pause_session.return_value = {
        "session_id": "test-session-uuid",
        "state": "paused",
        "remaining_seconds": 1700,
    }
    mock_service.resume_session.return_value = {
        "session_id": "test-session-uuid",
        "state": "active",
        "remaining_seconds": 1700,
    }
    mock_service.end_session.return_value = {
        "session_id": "test-session-uuid",
        "state": "completed",
        "elapsed_seconds": 100,
    }
    mock_service.can_reconnect.return_value = True
    mock_service.get_session_state.return_value = {
        "session_id": "test-session-uuid",
        "state": "active",
    }

    from features.sessions import dependencies as deps
    original_factory = deps.get_session_service
    deps.get_session_service = lambda: mock_service

    yield

    deps.get_session_service = original_factory


# ── Helper to bypass auth for tests ──────────────────────────────────────────


def _patch_auth():
    """Override the auth dependency to return a fake user."""
    from features.auth import guard as auth_guard
    original = auth_guard.get_current_user

    class FakeUser:
        id = "00000000-0000-0000-0000-000000000001"
        email = "test@test.com"
        username = "testuser"
        display_name = "Test User"

    async def mock_get_current_user():
        return FakeUser()

    auth_guard.get_current_user = mock_get_current_user
    return original


def _restore_auth(original):
    from features.auth import guard as auth_guard
    auth_guard.get_current_user = original


# ── Tests ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_start_session_endpoint_returns_session_id():
    """Verify POST /sessions creates a session."""
    orig = _patch_auth()
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/sessions",
                json={"interview_id": "00000000-0000-0000-0000-000000000001"},
            )
        assert response.status_code in (200, 201)
        data = response.json()
        assert "session_id" in data.get("data", {})
    finally:
        _restore_auth(orig)


@pytest.mark.asyncio
async def test_session_status_returns_state():
    """Verify GET /sessions/{id} returns session state."""
    orig = _patch_auth()
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/sessions/test-session-uuid")
        assert response.status_code == 200
        data = response.json()
        assert "state" in data.get("data", {})
    finally:
        _restore_auth(orig)


@pytest.mark.asyncio
async def test_pause_endpoint_returns_paused():
    """Verify POST /sessions/{id}/pause returns paused state."""
    orig = _patch_auth()
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/sessions/test-session-uuid/pause", json={})
        assert response.status_code == 200
        assert response.json()["data"]["state"] == "paused"
    finally:
        _restore_auth(orig)


@pytest.mark.asyncio
async def test_resume_endpoint_returns_active():
    """Verify POST /sessions/{id}/resume returns active state."""
    orig = _patch_auth()
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/sessions/test-session-uuid/resume", json={})
        assert response.status_code == 200
        assert response.json()["data"]["state"] == "active"
    finally:
        _restore_auth(orig)


@pytest.mark.asyncio
async def test_end_session_endpoint_returns_completed():
    """Verify POST /sessions/{id}/end returns completed state."""
    orig = _patch_auth()
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/sessions/test-session-uuid/end", json={})
        assert response.status_code == 200
        assert response.json()["data"]["state"] == "completed"
    finally:
        _restore_auth(orig)


@pytest.mark.asyncio
async def test_reconnect_check_returns_status():
    """Verify GET /sessions/{id}/reconnect returns reconnect status."""
    orig = _patch_auth()
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/sessions/test-session-uuid/reconnect")
        assert response.status_code == 200
        data = response.json()["data"]
        assert "can_reconnect" in data
        assert data["can_reconnect"] is True
    finally:
        _restore_auth(orig)
