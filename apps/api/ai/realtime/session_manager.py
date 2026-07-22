"""Session manager — in-memory registry for active interview sessions.

Each session holds its state, memory, transcript, and orchestrator.
Redis persistence is used for multi-server resilience.
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from ai.openai_provider import OpenAIProvider
from ai.provider import AIProvider
from ai.realtime.event_dispatcher import (
    EVENT_SESSION_ARCHIVED,
    EVENT_SESSION_COMPLETED,
    EVENT_SESSION_CREATED,
    EVENT_SESSION_FAILED,
    EVENT_SESSION_PAUSED,
    EVENT_SESSION_PREPARING,
    EVENT_SESSION_RESUMED,
    EVENT_SESSION_STARTED,
    EVENT_SESSION_TIMEOUT,
    EventDispatcher,
)
from ai.realtime.heartbeat import HeartbeatMonitor
from ai.realtime.memory_manager import ConversationMemory
from ai.realtime.orchestrator import AIOrchestrator
from ai.realtime.prompt_builder import PromptBuilder
from ai.realtime.state_machine import (
    InvalidTransitionError,
    SessionState,
    is_terminal,
    validate_transition,
)
from ai.realtime.telemetry import PerformanceTelemetry
from ai.realtime.transcript_manager import TranscriptManager

logger = logging.getLogger(__name__)

GRACE_PERIOD_SECONDS = 30
DEFAULT_DURATION_MINUTES = 30


@dataclass
class Session:
    """In-memory representation of an active interview session.

    Enhanced with recording metadata and performance telemetry.
    """

    session_id: str
    interview_id: str
    user_id: str
    state: SessionState = SessionState.IDLE
    config: dict[str, Any] | None = None

    # ── Runtime components ────────────────────────────────────────────────
    memory: ConversationMemory | None = None
    transcript: TranscriptManager | None = None
    orchestrator: AIOrchestrator | None = None

    # ── Timing ────────────────────────────────────────────────────────────
    connected_at: float | None = None
    paused_at: float | None = None
    total_paused_seconds: int = 0
    started_at: float | None = None
    preparing_at: float | None = None
    completed_at: float | None = None
    archived_at: float | None = None

    # ── Connection tracking ────────────────────────────────────────────────
    disconnect_count: int = 0
    last_disconnect_at: float | None = None
    last_reconnect_at: float | None = None
    error_count: int = 0
    last_error: str | None = None

    # ── Recording metadata ────────────────────────────────────────────────
    recording_url: str | None = None
    recording_duration_s: float = 0.0
    transcript_url: str | None = None
    prompt_version: str = ""

    # ── Event markers (for replay / debugging) ─────────────────────────────
    event_markers: list[dict] = field(default_factory=list)
    question_timestamps: list[dict] = field(default_factory=list)
    pause_timestamps: list[dict] = field(default_factory=list)

    # ── Extensible metadata ────────────────────────────────────────────────
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def elapsed_seconds(self) -> int:
        if self.started_at is None:
            return 0
        end = self.completed_at or time.time()
        return int(end - self.started_at - self.total_paused_seconds)

    @property
    def remaining_seconds(self) -> int:
        duration = (self.config or {}).get("duration_minutes", DEFAULT_DURATION_MINUTES) * 60
        return max(0, duration - self.elapsed_seconds)


class SessionNotFoundError(KeyError):
    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        super().__init__(f"Session not found: {session_id}")


class SessionManager:
    """Manages the lifecycle of all active interview sessions.

    Sessions live in memory.  Snapshots are written to the DB
    at key transition points for recovery and persistence.
    """

    def __init__(
        self,
        dispatcher: EventDispatcher,
        heartbeat_monitor: HeartbeatMonitor,
        prompt_builder: PromptBuilder | None = None,
        ai_provider: AIProvider | None = None,
    ) -> None:
        self._dispatcher = dispatcher
        self._heartbeat = heartbeat_monitor
        self._prompt_builder = prompt_builder or PromptBuilder()
        self._ai_provider = ai_provider or OpenAIProvider()
        self._sessions: dict[str, Session] = {}
        self._telemetry = PerformanceTelemetry()

    # ── Lifecycle ─────────────────────────────────────────────────────────

    # ── Lifecycle ─────────────────────────────────────────────────────────

    async def create_session(
        self,
        interview_id: str,
        user_id: str,
        config: dict[str, Any] | None = None,
    ) -> Session:
        """Create a new session in IDLE state."""
        session_id = str(uuid.uuid4())
        session = Session(
            session_id=session_id,
            interview_id=interview_id,
            user_id=user_id,
            config=config,
        )
        self._sessions[session_id] = session
        self._heartbeat.register(session_id)
        self._add_marker(session, "session.created")
        await self._dispatcher.emit(session_id, EVENT_SESSION_CREATED, {"interview_id": interview_id})
        logger.info("Session created: %s (interview=%s)", session_id[:8], interview_id[:8])
        return session

    async def prepare_session(
        self,
        session_id: str,
    ) -> Session:
        """Transition from IDLE → PREPARING.  Build the AI context."""
        session = self._get(session_id)
        self._transition(session, SessionState.PREPARING)
        session.preparing_at = time.time()

        config = session.config or {}
        self._add_marker(session, "session.prepare.start")

        system_prompt = self._prompt_builder.build_system_prompt(
            interview_type=config.get("type", "coding"),
            company=config.get("company", ""),
            role=config.get("role", ""),
            experience_level=config.get("experience_level", "mid-senior"),
            language=config.get("language"),
            framework=config.get("framework"),
            difficulty=config.get("difficulty"),
            duration_minutes=config.get("duration_minutes", 30),
            spoken_language=config.get("spoken_language", "en"),
            system_design_problem=config.get("system_design_problem"),
            resume_context=config.get("resume_context"),
            jd_context=config.get("jd_context"),
            custom_instructions=config.get("custom_instructions"),
        )

        memory = ConversationMemory(system_prompt=system_prompt)
        transcript = TranscriptManager()
        orchestrator = AIOrchestrator(
            provider=self._ai_provider,
            prompt_builder=self._prompt_builder,
            memory=memory,
            transcript=transcript,
        )

        session.memory = memory
        session.transcript = transcript
        session.orchestrator = orchestrator

        self._add_marker(session, "session.prepare.complete")
        await self._dispatcher.emit(session_id, EVENT_SESSION_PREPARING)
        return session

    async def start_session(self, session_id: str) -> Session:
        """Transition from PREPARING → ACTIVE.  Generate first question."""
        session = self._ensure_prepared(session_id)
        self._transition(session, SessionState.ACTIVE)
        session.connected_at = time.time()
        session.started_at = time.time()
        self._telemetry.session_started(session_id)
        self._add_marker(session, "session.started")

        assert session.orchestrator is not None
        first_question = await session.orchestrator.generate_initial_question()
        session.metadata["first_question"] = first_question

        await self._dispatcher.emit(
            session_id,
            EVENT_SESSION_STARTED,
            {
                "started_at": session.started_at,
                "duration_minutes": (session.config or {}).get("duration_minutes", DEFAULT_DURATION_MINUTES),
            },
        )
        return session

    async def pause_session(self, session_id: str) -> Session:
        """Transition ACTIVE/COMPLETING → PAUSED."""
        session = self._get(session_id)
        self._transition(session, SessionState.PAUSED)
        session.paused_at = time.time()
        session.pause_timestamps.append({"paused_at": session.paused_at})
        self._add_marker(session, "session.paused")
        await self._dispatcher.emit(session_id, EVENT_SESSION_PAUSED)
        return session

    async def resume_session(self, session_id: str) -> Session:
        """Transition PAUSED → ACTIVE."""
        session = self._get(session_id)
        if session.paused_at is not None:
            session.total_paused_seconds += int(time.time() - session.paused_at)
            session.paused_at = None
        self._transition(session, SessionState.ACTIVE)
        self._add_marker(session, "session.resumed")
        await self._dispatcher.emit(session_id, EVENT_SESSION_RESUMED)
        return session

    async def complete_session(self, session_id: str) -> Session:
        """Transition ACTIVE/PAUSED → COMPLETING → COMPLETED."""
        session = self._get(session_id)
        self._transition(session, SessionState.COMPLETING)

        assert session.orchestrator is not None
        await session.orchestrator.generate_wrap_up()

        self._transition(session, SessionState.COMPLETED)
        session.completed_at = time.time()
        self._heartbeat.unregister(session_id)
        self._add_marker(session, "session.completed")

        session_metrics = self._telemetry.session_ended(session_id)

        await self._dispatcher.emit(
            session_id,
            EVENT_SESSION_COMPLETED,
            {
                "elapsed_seconds": session.elapsed_seconds,
                "transcript_segments": session.transcript.segment_count if session.transcript else 0,
                "metrics": session_metrics,
            },
        )
        return session

    async def archive_session(self, session_id: str) -> Session:
        """Transition COMPLETED → ARCHIVED.

        Marks the session as archived after evaluation and long-term storage.
        """
        session = self._get(session_id)
        self._transition(session, SessionState.ARCHIVED)
        session.archived_at = time.time()
        session.recording_duration_s = session.elapsed_seconds
        self._add_marker(session, "session.archived")
        await self._dispatcher.emit(session_id, EVENT_SESSION_ARCHIVED)
        return session

    async def fail_session(self, session_id: str, error: str) -> Session:
        """Transition any active state → FAILED."""
        session = self._get(session_id)
        try:
            self._transition(session, SessionState.FAILED)
        except InvalidTransitionError:
            session.state = SessionState.FAILED
        session.error_count += 1
        session.last_error = error
        session.completed_at = time.time()
        self._heartbeat.unregister(session_id)
        self._add_marker(session, "session.failed", {"error": error})
        await self._dispatcher.emit(session_id, EVENT_SESSION_FAILED, {"error": error})
        return session

    async def timeout_session(self, session_id: str) -> Session:
        """Transition → TIMEOUT, then to COMPLETED."""
        session = self._get(session_id)
        try:
            self._transition(session, SessionState.TIMEOUT)
        except InvalidTransitionError:
            session.state = SessionState.TIMEOUT
        session.completed_at = time.time()
        self._heartbeat.unregister(session_id)
        self._add_marker(session, "session.timeout")
        await self._dispatcher.emit(session_id, EVENT_SESSION_TIMEOUT)
        self._transition(session, SessionState.COMPLETED)
        return session

    # ── Helpers ──────────────────────────────────────────────────────────

    def _add_marker(self, session: Session, event: str, extra: dict | None = None) -> None:
        """Append an event marker for replay and debugging."""
        session.event_markers.append(
            {
                "event": event,
                "timestamp": time.time(),
                "state": session.state.value,
                **(extra or {}),
            }
        )

    # ── WebSocket / Connection ────────────────────────────────────────────

    def record_disconnect(self, session_id: str) -> Session:
        session = self._get(session_id)
        session.disconnect_count += 1
        session.last_disconnect_at = time.time()
        return session

    def can_reconnect(self, session_id: str) -> bool:
        session = self._get(session_id)
        if is_terminal(session.state):
            return False
        if session.last_disconnect_at is None:
            return True
        elapsed = time.time() - session.last_disconnect_at
        return elapsed < GRACE_PERIOD_SECONDS

    # ── Query ─────────────────────────────────────────────────────────────

    def get_session(self, session_id: str) -> Session | None:
        return self._sessions.get(session_id)

    def get_user_session(self, user_id: str) -> Session | None:
        for session in self._sessions.values():
            if session.user_id == user_id and not is_terminal(session.state):
                return session
        return None

    def list_active(self) -> list[Session]:
        return [s for s in self._sessions.values() if not is_terminal(s.state)]

    def remove_session(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)
        self._heartbeat.unregister(session_id)

    def record_heartbeat(self, session_id: str) -> None:
        """Record a heartbeat ping from the client."""
        self._heartbeat.record_heartbeat(session_id)

    def snapshot(self, session_id: str) -> dict[str, Any] | None:
        session = self._get(session_id)
        memory_snapshot = session.memory.snapshot() if session.memory else None
        return {
            "session_id": session.session_id,
            "interview_id": session.interview_id,
            "user_id": session.user_id,
            "state": session.state.value,
            "config": session.config,
            "memory": memory_snapshot,
            "elapsed_seconds": session.elapsed_seconds,
            "remaining_seconds": session.remaining_seconds,
            "total_paused_seconds": session.total_paused_seconds,
            "disconnect_count": session.disconnect_count,
            "error_count": session.error_count,
        }

    # ── Validation ────────────────────────────────────────────────────────

    def _get(self, session_id: str) -> Session:
        session = self._sessions.get(session_id)
        if session is None:
            raise SessionNotFoundError(session_id)
        return session

    def _ensure_prepared(self, session_id: str) -> Session:
        session = self._get(session_id)
        if session.memory is None:
            raise ValueError(f"Session {session_id[:8]} has not been initialized")
        return session

    def _transition(self, session: Session, to_state: SessionState) -> None:
        validate_transition(session.state, to_state)
        session.state = to_state
