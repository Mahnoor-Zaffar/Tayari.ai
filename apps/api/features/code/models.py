"""SQLAlchemy ORM models for the coding interview feature."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base, JSONBType, UUIDType


def _now() -> datetime:
    return datetime.now(UTC)


class Problem(Base):
    """A coding challenge with visible and hidden test cases."""

    __tablename__ = "problems"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(80), nullable=False, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False)
    # easy | medium | hard

    description: Mapped[str] = mapped_column(Text, nullable=False)
    examples: Mapped[dict] = mapped_column(JSONBType, default=list)
    constraints: Mapped[dict] = mapped_column(JSONBType, default=list)
    # Each test case: {"id", "input", "expected_output", "is_hidden"}
    test_cases: Mapped[dict] = mapped_column(JSONBType, default=list)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    submissions = relationship("Submission", back_populates="problem")


class Submission(Base):
    """A user's code submission during an interview."""

    __tablename__ = "submissions"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    interview_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("interviews.id"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("users.id"), nullable=False, index=True)
    problem_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, ForeignKey("problems.id"), nullable=True, index=True)
    language: Mapped[str] = mapped_column(String(20), nullable=False)
    source_code: Mapped[str] = mapped_column(Text, nullable=False)

    status: Mapped[str] = mapped_column(String(20), default="queued", index=True)
    # queued → compiling → running → judging → completed | error | timeout

    test_results: Mapped[dict] = mapped_column(JSONBType, default=list)
    passed_count: Mapped[int] = mapped_column(Integer, default=0)
    total_count: Mapped[int] = mapped_column(Integer, default=0)
    execution_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    stdout: Mapped[str | None] = mapped_column(Text, nullable=True)
    stderr: Mapped[str | None] = mapped_column(Text, nullable=True)
    compiler_output: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    interview = relationship("Interview", backref="submissions")
    problem = relationship("Problem", back_populates="submissions")


class CodeReview(Base):
    """AI-generated code review for a submission."""

    __tablename__ = "code_reviews"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    submission_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("submissions.id"), nullable=False, unique=True, index=True
    )
    interview_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("interviews.id"), nullable=False, index=True)
    overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    dimensions: Mapped[dict] = mapped_column(JSONBType, default=dict)
    strengths: Mapped[dict] = mapped_column(JSONBType, default=list)
    improvements: Mapped[dict] = mapped_column(JSONBType, default=list)
    line_comments: Mapped[dict] = mapped_column(JSONBType, default=list)
    raw_review: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_used: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    submission = relationship("Submission", backref="code_review", uselist=False)
