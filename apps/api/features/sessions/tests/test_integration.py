"""Integration tests for the sessions feature.

Tests the full lifecycle: REST API → Session Manager → Persistence.
Uses FastAPI dependency_overrides for mocked auth and service.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from features.auth.guard import CurrentUser, get_current_user
from features.sessions.dependencies import get_session_service
from features.sessions.service import SessionService

# ── Mock factories ───────────────────────────────────────────────────────────


def _make_user() -> CurrentUser:
    return CurrentUser(
        id="00000000-0000-0000-0000-000000000001",
        email="test@test.com",
        username="testuser",
        display_name="Test User",
        email_verified=True,
        is_active=True,
        roles=["user"],
        permissions=["interview:read", "interview:write"],
    )


def _make_mock_service() -> AsyncMock:
    mock = AsyncMock(spec=SessionService)
    mock.start_session.return_value = {
        "session_id": "test-session-uuid",
        "interview_id": "test-interview-uuid",
        "status": "active",
        "initial_question": "Welcome! Tell me about yourself.",
    }
    mock.get_status.return_value = {
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
    mock.pause_session.return_value = {
        "session_id": "test-session-uuid",
        "state": "paused",
        "remaining_seconds": 1700,
    }
    mock.resume_session.return_value = {
        "session_id": "test-session-uuid",
        "state": "active",
        "remaining_seconds": 1700,
    }
    mock.end_session.return_value = {
        "session_id": "test-session-uuid",
        "state": "completed",
        "elapsed_seconds": 100,
    }
    mock.can_reconnect.return_value = True
    mock.get_session_state.return_value = {
        "session_id": "test-session-uuid",
        "state": "active",
    }
    return mock


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _override_dependencies():
    """Override FastAPI dependencies for all tests in this module."""
    from main import app

    mock_service = _make_mock_service()
    app.dependency_overrides[get_session_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: _make_user()

    yield

    app.dependency_overrides.clear()


# ── Tests ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_start_session_endpoint_returns_session_id():
    """Verify POST /sessions creates a session."""
    from main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/sessions",
            json={"interview_id": "00000000-0000-0000-0000-000000000001"},
        )
    assert response.status_code in (200, 201)
    data = response.json()
    assert "session_id" in data.get("data", {})


@pytest.mark.asyncio
async def test_session_status_returns_state():
    """Verify GET /sessions/{id} returns session state."""
    from main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/sessions/test-session-uuid")
    assert response.status_code == 200
    data = response.json()
    assert "state" in data.get("data", {})


@pytest.mark.asyncio
async def test_pause_endpoint_returns_paused():
    """Verify POST /sessions/{id}/pause returns paused state."""
    from main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/sessions/test-session-uuid/pause", json={})
    assert response.status_code == 200
    assert response.json()["data"]["state"] == "paused"


@pytest.mark.asyncio
async def test_resume_endpoint_returns_active():
    """Verify POST /sessions/{id}/resume returns active state."""
    from main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/sessions/test-session-uuid/resume", json={})
    assert response.status_code == 200
    assert response.json()["data"]["state"] == "active"


@pytest.mark.asyncio
async def test_end_session_endpoint_returns_completed():
    """Verify POST /sessions/{id}/end returns completed state."""
    from main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/sessions/test-session-uuid/end", json={})
    assert response.status_code == 200
    assert response.json()["data"]["state"] == "completed"


@pytest.mark.asyncio
async def test_reconnect_check_returns_status():
    """Verify GET /sessions/{id}/reconnect returns reconnect status."""
    from main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/sessions/test-session-uuid/reconnect")
    assert response.status_code == 200
    data = response.json()["data"]
    assert "can_reconnect" in data
    assert data["can_reconnect"] is True
