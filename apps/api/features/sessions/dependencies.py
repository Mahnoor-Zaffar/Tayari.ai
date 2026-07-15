"""Session feature dependency injection.

Wires the runtime modules (session manager, event dispatcher,
heartbeat monitor) into the service layer.
"""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ai.openai_provider import OpenAIProvider
from ai.realtime.event_dispatcher import EventDispatcher
from ai.realtime.heartbeat import HeartbeatMonitor
from ai.realtime.prompt_builder import PromptBuilder
from ai.realtime.session_manager import SessionManager
from core.database import get_db
from features.interview.repository import InterviewRepository
from features.sessions.repository import SessionRepository
from features.sessions.service import SessionService

# ── Singleton instances ──────────────────────────────────────────────────────

_dispatcher: EventDispatcher | None = None
_heartbeat: HeartbeatMonitor | None = None
_session_manager: SessionManager | None = None


def get_event_dispatcher() -> EventDispatcher:
    global _dispatcher
    if _dispatcher is None:
        _dispatcher = EventDispatcher()
    return _dispatcher


def get_heartbeat_monitor() -> HeartbeatMonitor:
    global _heartbeat
    if _heartbeat is None:
        dispatcher = get_event_dispatcher()
        _heartbeat = HeartbeatMonitor(dispatcher)
        _heartbeat.start()
    return _heartbeat


def get_session_manager() -> SessionManager:
    global _session_manager
    if _session_manager is None:
        dispatcher = get_event_dispatcher()
        heartbeat = get_heartbeat_monitor()
        prompt_builder = PromptBuilder()
        ai_provider = OpenAIProvider()
        _session_manager = SessionManager(
            dispatcher=dispatcher,
            heartbeat_monitor=heartbeat,
            prompt_builder=prompt_builder,
            ai_provider=ai_provider,
        )
    return _session_manager


# ── Request-scoped dependencies ──────────────────────────────────────────────


async def get_session_service(
    db: AsyncSession = Depends(get_db),
) -> SessionService:
    """Request-scoped SessionService with singleton runtime."""
    manager = get_session_manager()
    dispatcher = get_event_dispatcher()
    session_repo = SessionRepository(db)
    interview_repo = InterviewRepository(db)
    return SessionService(
        session_manager=manager,
        event_dispatcher=dispatcher,
        session_repo=session_repo,
        interview_repo=interview_repo,
    )
