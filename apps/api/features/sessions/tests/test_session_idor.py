"""Regression tests for session IDOR protection.

Every REST session operation must verify that the authenticated user owns the
session.  These tests confirm:
  - The session owner can access/modify their session.
  - A different authenticated user receives 403.
  - A nonexistent session returns 404.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from ai.realtime.session_manager import SessionNotFoundError
from core.errors import AuthorizationError
from features.sessions.service import SessionService

# ── Helpers ──────────────────────────────────────────────────────────────────


def _make_session(session_id: str, user_id: str, state: str = "active"):
    """Return a mock session dataclass-like object."""
    session = MagicMock()
    session.session_id = session_id
    session.interview_id = str(uuid4())
    session.user_id = user_id
    session.state = MagicMock(value=state)
    session.elapsed_seconds = 120
    session.remaining_seconds = 1680
    session.total_paused_seconds = 0
    session.disconnect_count = 0
    session.error_count = 0
    session.last_error = None
    session.started_at = None
    session.completed_at = None
    session.metadata = {"first_question": "Hello"}
    session.transcript = None
    return session


@pytest.fixture
def owner_id() -> UUID:
    return uuid4()


@pytest.fixture
def other_user_id() -> UUID:
    return uuid4()


@pytest.fixture
def session_id() -> str:
    return str(uuid4())


@pytest.fixture
def service(session_id, owner_id):
    """Build a SessionService with a mocked session belonging to owner_id."""
    session = _make_session(session_id, str(owner_id))

    manager = MagicMock()
    manager.get_session.return_value = session
    manager.pause_session = AsyncMock(return_value=session)
    manager.resume_session = AsyncMock(return_value=session)
    manager.complete_session = AsyncMock(return_value=session)
    manager.can_reconnect.return_value = True
    manager.snapshot.return_value = {"state": "active"}

    dispatcher = MagicMock(spec=["subscribe"])
    session_repo = AsyncMock()
    interview_repo = AsyncMock()

    svc = SessionService(
        session_manager=manager,
        event_dispatcher=dispatcher,
        session_repo=session_repo,
        interview_repo=interview_repo,
    )
    return svc


# ── Owner succeeds ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_owner_can_get_status(service, session_id, owner_id):
    result = await service.get_status(session_id, user_id=owner_id)
    assert result["session_id"] == session_id


@pytest.mark.asyncio
async def test_owner_can_pause(service, session_id, owner_id):
    result = await service.pause_session(session_id, user_id=owner_id)
    assert result["session_id"] == session_id


@pytest.mark.asyncio
async def test_owner_can_resume(service, session_id, owner_id):
    result = await service.resume_session(session_id, user_id=owner_id)
    assert result["session_id"] == session_id


@pytest.mark.asyncio
async def test_owner_can_end(service, session_id, owner_id):
    result = await service.end_session(session_id, user_id=owner_id)
    assert result["session_id"] == session_id


@pytest.mark.asyncio
async def test_owner_can_reconnect(service, session_id, owner_id):
    result = await service.can_reconnect(session_id, user_id=owner_id)
    assert result is True


@pytest.mark.asyncio
async def test_owner_can_get_state(service, session_id, owner_id):
    result = await service.get_session_state(session_id, user_id=owner_id)
    assert result is not None


# ── Different user gets 403 ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_other_user_cannot_get_status(service, session_id, other_user_id):
    with pytest.raises(AuthorizationError):
        await service.get_status(session_id, user_id=other_user_id)


@pytest.mark.asyncio
async def test_other_user_cannot_pause(service, session_id, other_user_id):
    with pytest.raises(AuthorizationError):
        await service.pause_session(session_id, user_id=other_user_id)


@pytest.mark.asyncio
async def test_other_user_cannot_resume(service, session_id, other_user_id):
    with pytest.raises(AuthorizationError):
        await service.resume_session(session_id, user_id=other_user_id)


@pytest.mark.asyncio
async def test_other_user_cannot_end(service, session_id, other_user_id):
    with pytest.raises(AuthorizationError):
        await service.end_session(session_id, user_id=other_user_id)


@pytest.mark.asyncio
async def test_other_user_cannot_reconnect(service, session_id, other_user_id):
    with pytest.raises(AuthorizationError):
        await service.can_reconnect(session_id, user_id=other_user_id)


@pytest.mark.asyncio
async def test_other_user_cannot_get_state(service, session_id, other_user_id):
    with pytest.raises(AuthorizationError):
        await service.get_session_state(session_id, user_id=other_user_id)


# ── Nonexistent session returns 404 ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_nonexistent_session_status(service, owner_id):
    service._manager.get_session.return_value = None
    with pytest.raises(SessionNotFoundError):
        await service.get_status("nonexistent", user_id=owner_id)


@pytest.mark.asyncio
async def test_nonexistent_session_pause(service, owner_id):
    service._manager.get_session.return_value = None
    with pytest.raises(SessionNotFoundError):
        await service.pause_session("nonexistent", user_id=owner_id)


@pytest.mark.asyncio
async def test_nonexistent_session_reconnect(service, owner_id):
    service._manager.get_session.return_value = None
    with pytest.raises(SessionNotFoundError):
        await service.can_reconnect("nonexistent", user_id=owner_id)


# ── Unauthenticated REST calls rejected at the dependency layer (401) ─────────


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/sessions/{sid}"),
        ("POST", "/sessions/{sid}/pause"),
        ("POST", "/sessions/{sid}/resume"),
        ("POST", "/sessions/{sid}/end"),
        ("GET", "/sessions/{sid}/reconnect"),
    ],
)
@pytest.mark.asyncio
async def test_unauthenticated_rest_call_rejected(method, path):
    """No token → 401 before the handler (and thus the ownership guard) runs."""
    from httpx import ASGITransport, AsyncClient

    from features.auth.guard import get_current_user
    from main import app

    sid = str(uuid4())
    previous = app.dependency_overrides.pop(get_current_user, None)
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test/api/v1") as unauth:
            response = await unauth.request(method, path.format(sid=sid))
        assert response.status_code == 401
    finally:
        if previous is not None:
            app.dependency_overrides[get_current_user] = previous
