"""Failure scenario tests for the session runtime.

Tests error handling, edge cases, and recovery paths.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from ai.provider import AIResponse
from ai.realtime.event_dispatcher import EventDispatcher
from ai.realtime.heartbeat import HeartbeatMonitor
from ai.realtime.prompt_builder import PromptBuilder
from ai.realtime.session_manager import (
    InvalidTransitionError,
    SessionManager,
    SessionNotFoundError,
    SessionState,
)


@pytest.fixture
def failing_provider():
    """Provider that fails after N calls."""
    provider = AsyncMock()
    call_count = [0]

    async def fail_after_two(*args, **kwargs):
        call_count[0] += 1
        if call_count[0] > 2:
            raise ValueError("AI provider unavailable")
        return AIResponse(content="Question?", model="gpt-4o-mini")

    provider.chat.side_effect = fail_after_two
    return provider


@pytest.fixture
def manager():
    dispatcher = EventDispatcher()
    heartbeat = HeartbeatMonitor(dispatcher)
    prompt_builder = PromptBuilder()
    provider = AsyncMock()
    provider.chat.return_value = AIResponse(content="Hello", model="gpt-4o-mini")
    mgr = SessionManager(
        dispatcher=dispatcher,
        heartbeat_monitor=heartbeat,
        prompt_builder=prompt_builder,
        ai_provider=provider,
    )
    yield mgr
    mgr._sessions.clear()


@pytest.mark.asyncio
class TestFailureScenarios:
    async def test_create_session_with_empty_config(self, manager: SessionManager):
        """Session can be created with no config."""
        session = await manager.create_session(
            interview_id="i-1",
            user_id="u-1",
            config=None,
        )
        assert session.config is None
        assert session.state == SessionState.IDLE

    async def test_initialize_twice_raises(self, manager: SessionManager):
        """Cannot initialize an already-initialized session."""
        session = await manager.create_session("i-1", "u-1")
        await manager.prepare_session(session.session_id)
        with pytest.raises(InvalidTransitionError):
            await manager.prepare_session(session.session_id)

    async def test_complete_already_completed_fails(self, manager: SessionManager):
        """Cannot complete a session that is already completed."""
        session = await manager.create_session("i-1", "u-1")
        await manager.prepare_session(session.session_id)
        await manager.start_session(session.session_id)
        await manager.complete_session(session.session_id)
        with pytest.raises(InvalidTransitionError):
            await manager.complete_session(session.session_id)

    async def test_pause_from_pending_fails(self, manager: SessionManager):
        """Cannot pause a session that hasn't started."""
        session = await manager.create_session("i-1", "u-1")
        with pytest.raises(InvalidTransitionError):
            await manager.pause_session(session.session_id)

    async def test_resume_from_active_fails(self, manager: SessionManager):
        """Cannot resume an already active session."""
        session = await manager.create_session("i-1", "u-1")
        await manager.prepare_session(session.session_id)
        await manager.start_session(session.session_id)
        with pytest.raises(InvalidTransitionError):
            await manager.resume_session(session.session_id)

    async def test_reconnect_after_completed_fails(self, manager: SessionManager):
        """Cannot reconnect to a completed session."""
        session = await manager.create_session("i-1", "u-1")
        await manager.prepare_session(session.session_id)
        await manager.start_session(session.session_id)
        await manager.complete_session(session.session_id)
        await manager.archive_session(session.session_id)
        assert manager.can_reconnect(session.session_id) is False

    async def test_disconnect_reconnect_within_grace(self, manager: SessionManager):
        """Reconnection within grace period is allowed."""
        session = await manager.create_session("i-1", "u-1")
        await manager.prepare_session(session.session_id)
        await manager.start_session(session.session_id)
        manager.record_disconnect(session.session_id)
        assert manager.can_reconnect(session.session_id) is True

    async def test_missing_session_returns_none(self, manager: SessionManager):
        """get_session returns None for non-existent session."""
        assert manager.get_session("nonexistent") is None

    async def test_snapshot_nonexistent_session_fails(self, manager: SessionManager):
        """Snapshot raises for non-existent session."""
        with pytest.raises(SessionNotFoundError):
            manager.snapshot("nonexistent")

    async def test_remove_session_cleans_up(self, manager: SessionManager):
        """Removing a session cleans it from the registry."""
        session = await manager.create_session("i-1", "u-1")
        manager.remove_session(session.session_id)
        assert manager.get_session(session.session_id) is None

    async def test_fail_session_records_error(self, manager: SessionManager):
        """Failed session records the error message."""
        session = await manager.create_session("i-1", "u-1")
        await manager.fail_session(session.session_id, "Test error")
        session = manager.get_session(session.session_id)
        assert session is not None
        assert session.last_error == "Test error"
        assert session.state == SessionState.FAILED
