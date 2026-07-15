"""Session event repository.

Persists session events for audit logging and reconnection replay.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from features.sessions.models import SessionEvent


class SessionRepository:
    """Async repository for session event persistence."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

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
        result = await self._session.execute(
            select(SessionEvent.id).where(SessionEvent.session_id == session_id)
        )
        return len(list(result.scalars().all()))
