"""Tests for the session manager."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

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
def mock_provider():
    provider = AsyncMock()
    provider.chat.return_value = AIResponse(
        content="Welcome to the interview. Can you tell me about yourself?",
        model="gpt-4o-mini",
        usage={"prompt_tokens": 50, "completion_tokens": 20},
    )
    provider.chat_stream.return_value = AsyncMock()
    provider.structured_output.return_value = {
        "overall_score": 4.0,
        "dimensions": {},
        "hire_verdict": "hire",
        "strengths": [],
        "improvements": [],
        "overall_assessment": "Good candidate.",
    }
    return provider


@pytest.fixture
def dispatcher():
    return EventDispatcher()


@pytest.fixture
def heartbeat(dispatcher):
    return HeartbeatMonitor(dispatcher)


@pytest.fixture
def prompt_builder():
    builder = MagicMock(spec=PromptBuilder)
    builder.build_system_prompt.return_value = "You are an interviewer at Google."
    return builder


@pytest.fixture
def manager(mock_provider, dispatcher, heartbeat, prompt_builder):
    mgr = SessionManager(
        dispatcher=dispatcher,
        heartbeat_monitor=heartbeat,
        prompt_builder=prompt_builder,
        ai_provider=mock_provider,
    )
    yield mgr
    mgr._sessions.clear()


@pytest.mark.asyncio
class TestSessionManager:
    async def test_create_session(self, manager: SessionManager):
        session = await manager.create_session(
            interview_id="interview-1",
            user_id="user-1",
            config={"type": "coding", "company": "Google", "duration_minutes": 30},
        )
        assert session.session_id is not None
        assert session.state == SessionState.IDLE
        assert session.interview_id == "interview-1"
        assert session.user_id == "user-1"

    async def test_create_and_initialize(self, manager: SessionManager):
        config = {"type": "coding", "company": "Google", "role": "SWE",
                  "experience_level": "mid-senior"}
        session = await manager.create_session(
            interview_id="i-1", user_id="u-1", config=config,
        )
        session = await manager.prepare_session(session.session_id)
        assert session.state == SessionState.PREPARING
        assert session.memory is not None
        assert session.orchestrator is not None
        assert session.transcript is not None

    async def test_full_lifecycle(self, manager: SessionManager):
        config = {"type": "coding", "company": "Google", "role": "SWE",
                  "experience_level": "mid-senior", "duration_minutes": 30}
        session = await manager.create_session(
            interview_id="i-1", user_id="u-1", config=config,
        )
        session = await manager.prepare_session(session.session_id)
        session = await manager.start_session(session.session_id)
        assert session.state == SessionState.ACTIVE
        assert session.started_at is not None
        assert "first_question" in session.metadata

        session = await manager.pause_session(session.session_id)
        assert session.state == SessionState.PAUSED

        session = await manager.resume_session(session.session_id)
        assert session.state == SessionState.ACTIVE

        session = await manager.complete_session(session.session_id)
        assert session.state == SessionState.COMPLETED
        assert session.completed_at is not None

    async def test_fail_session(self, manager: SessionManager):
        session = await manager.create_session("i-1", "u-1")
        failed = await manager.fail_session(session.session_id, "Network error")
        assert failed.state == SessionState.FAILED
        assert failed.last_error == "Network error"
        assert failed.error_count == 1

    async def test_session_not_found(self, manager: SessionManager):
        with pytest.raises(SessionNotFoundError):
            await manager.start_session("nonexistent")

    async def test_invalid_transition(self, manager: SessionManager):
        session = await manager.create_session("i-1", "u-1")
        with pytest.raises(InvalidTransitionError):
            await manager.pause_session(session.session_id)  # Can't pause from PENDING

    async def test_recording_disconnect(self, manager: SessionManager):
        session = await manager.create_session("i-1", "u-1")
        manager.record_disconnect(session.session_id)
        assert session.disconnect_count == 1
        assert session.last_disconnect_at is not None

    async def test_can_reconnect_within_grace(self, manager: SessionManager):
        session = await manager.create_session("i-1", "u-1")
        manager.record_disconnect(session.session_id)
        assert manager.can_reconnect(session.session_id) is True

    async def test_snapshot_includes_state(self, manager: SessionManager):
        session = await manager.create_session(
            interview_id="i-1", user_id="u-1",
            config={"duration_minutes": 30},
        )
        snap = manager.snapshot(session.session_id)
        assert snap is not None
        assert snap["session_id"] == session.session_id
        assert snap["state"] == SessionState.IDLE.value

    async def test_get_user_session(self, manager: SessionManager):
        await manager.create_session("i-1", "user-1")
        await manager.create_session("i-2", "user-2")
        found = manager.get_user_session("user-1")
        assert found is not None
        assert found.interview_id == "i-1"

    async def test_list_active(self, manager: SessionManager):
        s1 = await manager.create_session("i-1", "u-1")
        s2 = await manager.create_session("i-2", "u-2")
        active = manager.list_active()
        assert len(active) == 2

        await manager.fail_session(s1.session_id, "fail")
        active = manager.list_active()
        assert len(active) == 1
        assert active[0].session_id == s2.session_id

    async def test_remove_session(self, manager: SessionManager):
        session = await manager.create_session("i-1", "u-1")
        manager.remove_session(session.session_id)
        assert manager.get_session(session.session_id) is None
