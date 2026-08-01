"""Tests for the session service — mocked SessionManager, real service logic."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.realtime.session_manager import SessionNotFoundError
from features.sessions.service import SessionService


@pytest.fixture
def mock_manager():
    mgr = MagicMock()
    mgr.create_session = AsyncMock()
    mgr.prepare_session = AsyncMock()
    mgr.start_session = AsyncMock()
    mgr.pause_session = AsyncMock()
    mgr.resume_session = AsyncMock()
    mgr.complete_session = AsyncMock()
    mgr.get_session = MagicMock()
    mgr.snapshot = MagicMock()
    mgr.can_reconnect = MagicMock()
    mgr.record_disconnect = MagicMock()
    mgr.record_reconnect = MagicMock()
    mgr.set_current_question = MagicMock()
    mgr.record_heartbeat = MagicMock()
    mgr.remove_session = MagicMock()
    return mgr


@pytest.fixture
def mock_dispatcher():
    disp = MagicMock()
    disp.subscribe = MagicMock()
    disp.emit = AsyncMock()
    return disp


@pytest.fixture
def mock_session_repo():
    repo = MagicMock()
    repo.create_event = AsyncMock()
    repo.get_events = AsyncMock()
    repo.get_latest_sequence = AsyncMock(return_value=0)
    return repo


@pytest.fixture
def mock_interview_repo():
    repo = MagicMock()
    repo.update_status = AsyncMock()
    repo.update_transcript = AsyncMock()
    repo.get_interview_by_id = AsyncMock()
    repo.get_resume_with_content = AsyncMock()
    repo.get_job_description_with_content = AsyncMock()
    return repo


@pytest.fixture
def service(mock_manager, mock_dispatcher, mock_session_repo, mock_interview_repo):
    return SessionService(
        session_manager=mock_manager,
        event_dispatcher=mock_dispatcher,
        session_repo=mock_session_repo,
        interview_repo=mock_interview_repo,
    )


class TestSessionStart:
    @pytest.mark.asyncio
    async def test_creates_and_starts_session(self, service, mock_manager, mock_interview_repo):
        sid = uuid4()
        iid = uuid4()
        uid = uuid4()

        mock_interview_repo.get_interview_by_id.return_value = MagicMock(
            id=iid,
            type="coding",
            company="TestCo",
            role="Engineer",
            experience_level="mid-senior",
            language="python",
            spoken_language="en",
            framework=None,
            difficulty="medium",
            duration_minutes=30,
            custom_instructions=None,
            system_design_problem=None,
            resume_id=None,
            job_description_id=None,
            status="pending",
        )
        mock_session = MagicMock()
        mock_session.session_id = str(sid)
        mock_session.interview_id = str(iid)
        mock_session.state = MagicMock(value="active")
        mock_session.metadata = {"first_question": "What is your approach?"}
        mock_manager.create_session.return_value = mock_session
        mock_manager.start_session.return_value = mock_session

        result = await service.start_session(iid, uid)

        mock_manager.create_session.assert_called_once()
        mock_manager.prepare_session.assert_called_once()
        mock_manager.start_session.assert_called_once()
        mock_interview_repo.update_status.assert_called_with(iid, "active")
        assert result["initial_question"] == "What is your approach?"

    @pytest.mark.asyncio
    async def test_raises_on_missing_interview(self, service, mock_interview_repo):
        mock_interview_repo.get_interview_by_id.return_value = None
        with pytest.raises(ValueError, match="Interview not found"):
            await service.start_session(uuid4(), uuid4())

    @pytest.mark.asyncio
    async def test_raises_on_completed_interview(self, service, mock_interview_repo):
        mock_interview_repo.get_interview_by_id.return_value = MagicMock(
            status="completed",
            resume_id=None,
            job_description_id=None,
        )
        with pytest.raises(ValueError, match="already been completed"):
            await service.start_session(uuid4(), uuid4())


class TestSessionStatus:
    @pytest.mark.asyncio
    async def test_get_status_returns_snapshot(self, service, mock_manager):
        mock_manager.get_session.return_value = MagicMock(
            session_id="s1",
            interview_id="i1",
            user_id="u1",
            state=MagicMock(value="active"),
            elapsed_seconds=120,
            remaining_seconds=1680,
            total_paused_seconds=0,
            disconnect_count=0,
            error_count=0,
            last_error=None,
            started_at=1000,
            completed_at=None,
        )
        result = await service.get_status("s1")
        assert result["state"] == "active"

    @pytest.mark.asyncio
    async def test_get_status_raises_on_missing(self, service, mock_manager):
        mock_manager.get_session.return_value = None
        with pytest.raises(SessionNotFoundError):
            await service.get_status("missing")


class TestSessionPause:
    @pytest.mark.asyncio
    async def test_pauses_session(self, service, mock_manager):
        mock_session = MagicMock()
        mock_session.session_id = "s1"
        mock_session.state = MagicMock(value="paused")
        mock_session.remaining_seconds = 1500
        mock_manager.pause_session.return_value = mock_session
        result = await service.pause_session("s1")
        assert result["state"] == "paused"


class TestSessionEnd:
    @pytest.mark.asyncio
    async def test_completes_session(self, service, mock_manager, mock_interview_repo):
        mock_session = MagicMock()
        mock_session.session_id = "s1"
        mock_session.interview_id = str(uuid4())
        mock_session.state = MagicMock(value="completed")
        mock_session.elapsed_seconds = 600
        mock_session.transcript = MagicMock()
        mock_session.transcript.get_transcript.return_value = [{"speaker": "ai", "text": "Hello"}]
        mock_manager.get_session.return_value = mock_session
        mock_manager.complete_session.return_value = mock_session

        result = await service.end_session("s1")
        assert result["state"] == "completed"

    @pytest.mark.asyncio
    async def test_raises_on_missing_session(self, service, mock_manager):
        mock_manager.get_session.return_value = None
        with pytest.raises(SessionNotFoundError):
            await service.end_session("missing")


class TestAnswer:
    @pytest.mark.asyncio
    async def test_process_answer_returns_next_question(self, service, mock_manager):
        mock_session = MagicMock()
        mock_session.orchestrator = MagicMock()
        mock_session.orchestrator.process_answer = AsyncMock(return_value="Next question?")
        mock_manager.get_session.return_value = mock_session

        result = await service.process_answer("s1", "My answer")
        assert result == "Next question?"

    @pytest.mark.asyncio
    async def test_process_answer_returns_none_when_done(self, service, mock_manager):
        mock_session = MagicMock()
        mock_session.orchestrator = MagicMock()
        mock_session.orchestrator.process_answer = AsyncMock(return_value=None)
        mock_manager.get_session.return_value = mock_session

        result = await service.process_answer("s1", "My answer")
        assert result is None

    @pytest.mark.asyncio
    async def test_process_answer_raises_on_missing_session(self, service, mock_manager):
        mock_manager.get_session.return_value = None
        with pytest.raises(ValueError, match="Session or orchestrator not found"):
            await service.process_answer("missing", "answer")


class TestHint:
    @pytest.mark.asyncio
    async def test_request_hint_returns_hint(self, service, mock_manager):
        mock_session = MagicMock()
        mock_session.orchestrator = MagicMock()
        mock_session.orchestrator.generate_hint = AsyncMock(return_value="Try a hash map.")
        mock_manager.get_session.return_value = mock_session

        result = await service.request_hint("s1")
        assert result == "Try a hash map."

    @pytest.mark.asyncio
    async def test_request_hint_returns_none_on_missing(self, service, mock_manager):
        mock_manager.get_session.return_value = None
        result = await service.request_hint("missing")
        assert result is None


class TestReconnect:
    @pytest.mark.asyncio
    async def test_can_reconnect_delegates(self, service, mock_manager):
        mock_manager.can_reconnect.return_value = True
        result = await service.can_reconnect("s1")
        assert result is True

    def test_record_reconnect_handles_missing(self, service, mock_manager):
        mock_manager.record_reconnect.side_effect = Exception("gone")
        service.record_reconnect("missing")

    def test_set_current_question_handles_missing(self, service, mock_manager):
        mock_manager.set_current_question.side_effect = Exception("gone")
        service.set_current_question("missing", "What?")


class TestCleanup:
    def test_remove_session_delegates(self, service, mock_manager):
        service.remove_session("s1")
        mock_manager.remove_session.assert_called_once_with("s1")
