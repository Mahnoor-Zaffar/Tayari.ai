"""AI usage telemetry ORM model.

Persists one row per model gateway call so we can track model, tokens,
latency, cost, failures, and prompt version over time.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


def _now() -> datetime:
    return datetime.now(UTC)


class AIUsage(Base):
    __tablename__ = "ai_usage"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task: Mapped[str] = mapped_column(String(30), nullable=False)
    provider: Mapped[str] = mapped_column(String(30), nullable=False)
    model: Mapped[str] = mapped_column(String(80), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(30), nullable=True)
    interview_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    session_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    prompt_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completion_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    estimated_cost_cents: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_error: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_now, index=True)


def ai_usage_row_from_record(record: Any) -> dict[str, Any]:
    """Map a recorder.UsageRecord onto AIUsage column values (duck-typed)."""
    interview_id = record.interview_id
    session_id = record.session_id
    return {
        "task": record.task,
        "provider": record.provider,
        "model": record.model,
        "prompt_version": record.prompt_version,
        "interview_id": str(interview_id) if interview_id else None,
        "session_id": str(session_id) if session_id else None,
        "prompt_tokens": record.prompt_tokens,
        "completion_tokens": record.completion_tokens,
        "latency_ms": record.latency_ms,
        "estimated_cost_cents": record.estimated_cost_cents,
        "is_error": record.is_error,
        "error_message": record.error_message,
        "created_at": datetime.fromtimestamp(record.created_at, tz=UTC),
    }
