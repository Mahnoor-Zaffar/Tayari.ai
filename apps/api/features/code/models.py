"""SQLAlchemy ORM models for the coding interview feature."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


def _now() -> datetime:
    return datetime.now(UTC)


class Submission(Base):
    """A user's code submission during an interview."""

    __tablename__ = "submissions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interview_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("interviews.id"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    language: Mapped[str] = mapped_column(String(20), nullable=False)
    source_code: Mapped[str] = mapped_column(Text, nullable=False)

    status: Mapped[str] = mapped_column(String(20), default="queued", index=True)
    # queued → compiling → running → judging → completed | error | timeout

    test_results: Mapped[dict] = mapped_column(JSONB, default=list)
    passed_count: Mapped[int] = mapped_column(Integer, default=0)
    total_count: Mapped[int] = mapped_column(Integer, default=0)
    execution_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    stdout: Mapped[str | None] = mapped_column(Text, nullable=True)
    stderr: Mapped[str | None] = mapped_column(Text, nullable=True)
    compiler_output: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    interview = relationship("Interview", backref="submissions")


class CodeReview(Base):
    """AI-generated code review for a submission."""

    __tablename__ = "code_reviews"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("submissions.id"), nullable=False, unique=True, index=True
    )
    interview_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("interviews.id"), nullable=False, index=True
    )
    overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    dimensions: Mapped[dict] = mapped_column(JSONB, default=dict)
    strengths: Mapped[dict] = mapped_column(JSONB, default=list)
    improvements: Mapped[dict] = mapped_column(JSONB, default=list)
    line_comments: Mapped[dict] = mapped_column(JSONB, default=list)
    raw_review: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_used: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    submission = relationship("Submission", backref="code_review", uselist=False)
