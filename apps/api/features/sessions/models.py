"""Session event ORM model for event sourcing and reconnection replay."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


def _now() -> datetime:
    return datetime.now(UTC)


class SessionEvent(Base):
    """An auditable event in an interview session.

    Used for:
    - Event sourcing / audit log
    - Reconnection replay (client replays missed events)
    - Debugging and analytics
    """

    __tablename__ = "session_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    interview_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "session_id": self.session_id,
            "interview_id": str(self.interview_id),
            "event_type": self.event_type,
            "payload": self.payload,
            "sequence": self.sequence,
            "created_at": self.created_at.isoformat(),
        }
