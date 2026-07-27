"""Session event repository.

Persists session events for audit logging and reconnection replay.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from features.interview.models import Interview
from features.sessions.models import SessionEvent

_TERMINAL_STATES = frozenset({"completed", "cancelled", "archived"})


class SessionRepository:
    """Async repository for session event persistence."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_active_sessions(self) -> list[dict]:
        """Return session metadata for all non-terminal sessions.

        Finds distinct session_ids from ``session_events`` whose
        associated interview is still active (not completed/cancelled).
        """
        result = await self._session.execute(
            select(SessionEvent.session_id, SessionEvent.interview_id)
            .distinct(SessionEvent.session_id)
            .order_by(SessionEvent.session_id, SessionEvent.created_at.desc())
        )
        rows = result.all()

        active = []
        for row in rows:
            interview = await self._session.get(Interview, row.interview_id)
            if interview is None or interview.status in _TERMINAL_STATES:
                continue
            active.append(
                {
                    "session_id": row.session_id,
                    "interview_id": str(row.interview_id),
                    "user_id": str(interview.user_id),
                    "state": interview.status,
                    "config": None,
                    "current_question": None,
                    "current_question_type": "initial",
                }
            )
        return active

    async def create_event(
        self,
        session_id: str,
        interview_id: UUID,
        event_type: str,
        payload: dict | None = None,
        sequence: int = 0,
    ) -> SessionEvent:
        """Persist a session event."""
        event = SessionEvent(
            session_id=session_id,
            interview_id=interview_id,
            event_type=event_type,
            payload=payload or {},
            sequence=sequence,
        )
        self._session.add(event)
        await self._session.flush()
        await self._session.refresh(event)
        return event

    async def get_events(
        self,
        session_id: str,
        after_sequence: int = 0,
        limit: int = 100,
    ) -> list[SessionEvent]:
        """Return events for a session after a given sequence number."""
        result = await self._session.execute(
            select(SessionEvent)
            .where(
                SessionEvent.session_id == session_id,
                SessionEvent.sequence > after_sequence,
            )
            .order_by(SessionEvent.sequence.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_latest_sequence(self, session_id: str) -> int:
        """Return the highest sequence number for a session."""
        result = await self._session.execute(
            select(SessionEvent.sequence)
            .where(SessionEvent.session_id == session_id)
            .order_by(SessionEvent.sequence.desc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        return row if row is not None else -1

    async def count_events(self, session_id: str) -> int:
        """Count total events for a session."""
        result = await self._session.execute(select(SessionEvent.id).where(SessionEvent.session_id == session_id))
        return len(list(result.scalars().all()))
