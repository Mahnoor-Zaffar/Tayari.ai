"""Session service — orchestrates between HTTP/WS handlers and the runtime.

Coordinates session lifecycle with the in-memory SessionManager
and persists events to the database.
"""

from __future__ import annotations

import logging
from uuid import UUID

from ai.realtime.event_dispatcher import (
    EVENT_SESSION_COMPLETED,
    EVENT_SESSION_COMPLETING,
    EVENT_SESSION_CREATED,
    EVENT_SESSION_FAILED,
    EVENT_SESSION_PAUSED,
    EVENT_SESSION_RESUMED,
    EVENT_SESSION_STARTED,
    EventDispatcher,
)
from ai.realtime.session_manager import SessionManager, SessionNotFoundError
from features.interview.repository import InterviewRepository
from features.sessions.repository import SessionRepository

logger = logging.getLogger(__name__)


class SessionService:
    """Application service for interview sessions.

    Delegates to:
    - SessionManager (in-memory runtime)
    - SessionRepository (event persistence)
    - InterviewRepository (status updates)
    """

    def __init__(
        self,
        session_manager: SessionManager,
        event_dispatcher: EventDispatcher,
        session_repo: SessionRepository,
        interview_repo: InterviewRepository,
    ) -> None:
        self._manager = session_manager
        self._dispatcher = event_dispatcher
        self._session_repo = session_repo
        self._interview_repo = interview_repo

        # Wire up event → persistence
        self._dispatcher.subscribe(EVENT_SESSION_CREATED, self._on_event)
        self._dispatcher.subscribe(EVENT_SESSION_STARTED, self._on_event)
        self._dispatcher.subscribe(EVENT_SESSION_PAUSED, self._on_event)
        self._dispatcher.subscribe(EVENT_SESSION_RESUMED, self._on_event)
        self._dispatcher.subscribe(EVENT_SESSION_COMPLETING, self._on_event)
        self._dispatcher.subscribe(EVENT_SESSION_COMPLETED, self._on_event)
        self._dispatcher.subscribe(EVENT_SESSION_FAILED, self._on_event)

    # ── Public API ────────────────────────────────────────────────────────

    async def start_session(self, interview_id: UUID, user_id: UUID) -> dict:
        """Full lifecycle: create → initialize → start."""
        interview = await self._interview_repo.get_interview_by_id(interview_id, user_id)
        if interview is None:
            raise ValueError("Interview not found")

        config = {
            "type": interview.type,
            "company": interview.company,
            "role": interview.role,
            "experience_level": interview.experience_level,
            "language": interview.language,
            "framework": interview.framework,
            "duration_minutes": interview.duration_minutes,
            "custom_instructions": interview.custom_instructions,
            "resume_context": None,
            "jd_context": None,
        }

        session = await self._manager.create_session(
            interview_id=str(interview_id),
            user_id=str(user_id),
            config=config,
        )

        await self._manager.prepare_session(session.session_id)
        session = await self._manager.start_session(session.session_id)

        # Mark interview as active in DB
        await self._interview_repo.update_status(interview_id, "active")

        return {
            "session_id": session.session_id,
            "interview_id": session.interview_id,
            "status": session.state.value,
            "initial_question": session.metadata.get("first_question", ""),
        }

    async def get_status(self, session_id: str) -> dict:
        session = self._manager.get_session(session_id)
        if session is None:
            raise SessionNotFoundError(session_id)
        return {
            "session_id": session.session_id,
            "interview_id": session.interview_id,
            "user_id": session.user_id,
            "state": session.state.value,
            "elapsed_seconds": session.elapsed_seconds,
            "remaining_seconds": session.remaining_seconds,
            "total_paused_seconds": session.total_paused_seconds,
            "disconnect_count": session.disconnect_count,
            "error_count": session.error_count,
            "last_error": session.last_error,
            "started_at": session.started_at,
            "completed_at": session.completed_at,
        }

    async def pause_session(self, session_id: str) -> dict:
        session = await self._manager.pause_session(session_id)
        return {
            "session_id": session.session_id,
            "state": session.state.value,
            "remaining_seconds": session.remaining_seconds,
        }

    async def resume_session(self, session_id: str) -> dict:
        session = await self._manager.resume_session(session_id)
        return {
            "session_id": session.session_id,
            "state": session.state.value,
            "remaining_seconds": session.remaining_seconds,
        }

    async def end_session(self, session_id: str) -> dict:
        session = self._manager.get_session(session_id)
        if session is None:
            raise SessionNotFoundError(session_id)

        # Persist transcript to interview record before completing
        try:
            if session.transcript and session.interview_id:
                transcript = session.transcript.get_transcript()
                if transcript:
                    from uuid import UUID as _UUID

                    await self._interview_repo.update_transcript(_UUID(session.interview_id), transcript)
                    logger.info(
                        "Persisted %d transcript segments for interview %s",
                        len(transcript),
                        session.interview_id[:8],
                    )
        except Exception as exc:
            logger.error("Failed to persist transcript: %s (session=%s)", exc, session_id[:8])

        session = await self._manager.complete_session(session_id)

        # Mark interview as completed in DB
        try:
            await self._interview_repo.update_status(UUID(session.interview_id), "completed")
        except Exception as exc:
            logger.error("Failed to update interview status: %s (session=%s)", exc, session_id[:8])

        return {
            "session_id": session.session_id,
            "state": session.state.value,
            "elapsed_seconds": session.elapsed_seconds,
        }

    async def get_session_state(self, session_id: str) -> dict | None:
        return self._manager.snapshot(session_id)

    async def can_reconnect(self, session_id: str) -> bool:
        return self._manager.can_reconnect(session_id)

    async def process_answer(self, session_id: str, text: str) -> str | None:
        """Process a user answer and return the next AI question."""
        session = self._manager.get_session(session_id)
        if session is None or session.orchestrator is None:
            raise ValueError("Session or orchestrator not found")

        next_question = await session.orchestrator.process_answer(text)

        if next_question is None:
            await self._dispatcher.emit(session_id, EVENT_SESSION_COMPLETING)

        return next_question

    async def request_hint(self, session_id: str) -> str | None:
        session = self._manager.get_session(session_id)
        if session is None or session.orchestrator is None:
            return None
        return await session.orchestrator.generate_hint()

    # ── Public session access (replaces direct _manager access) ──────────

    def get_session(self, session_id: str) -> dict | None:
        """Return a public snapshot of a session, or None."""
        return self._manager.snapshot(session_id)

    def record_disconnect(self, session_id: str) -> None:
        """Record a WebSocket disconnect for a session."""
        try:
            self._manager.record_disconnect(session_id)
        except Exception:
            pass

    def record_heartbeat(self, session_id: str) -> None:
        """Record a heartbeat for a session."""
        self._manager.record_heartbeat(session_id)

    # ── Event Persistence ─────────────────────────────────────────────────

    async def _on_event(self, session_id: str, event_type: str, payload: dict) -> None:
        """Persist events to the database (subscriber callback)."""
        session = self._manager.get_session(session_id)
        if session is None:
            return
        try:
            sequence = await self._session_repo.get_latest_sequence(session_id) + 1
            await self._session_repo.create_event(
                session_id=session_id,
                interview_id=UUID(session.interview_id),
                event_type=event_type,
                payload=payload,
                sequence=sequence,
            )
        except Exception as exc:
            logger.error("Failed to persist event: %s (session=%s)", exc, session_id[:8])

    # ── Cleanup ───────────────────────────────────────────────────────────

    def remove_session(self, session_id: str) -> None:
        self._manager.remove_session(session_id)
