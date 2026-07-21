"""SQLAlchemy ORM models for the interview feature.

Tables:
    interviews              — A single interview session (1:1 with configuration)
    interview_configurations — Configuration chosen during the setup wizard
    resumes                  — Uploaded resume metadata + parsed text
    job_descriptions         — Uploaded JD metadata + parsed text
    interview_templates      — Pre-configured presets (FAANG frontend, etc.)
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


def _now() -> datetime:
    return datetime.now(UTC)


class Interview(Base):
    """A single interview session.

    Created at the end of the Setup wizard.  Links to its configuration,
    optional resume and job description uploads, and (eventually) an
    evaluation via the reports feature.
    """

    __tablename__ = "interviews"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    company: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    experience_level: Mapped[str] = mapped_column(String(20), nullable=False)
    language: Mapped[str | None] = mapped_column(String(20), nullable=True)
    spoken_language: Mapped[str | None] = mapped_column(String(10), nullable=True, default="en")
    difficulty: Mapped[str] = mapped_column(String(10), nullable=False, default="medium")
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    framework: Mapped[str | None] = mapped_column(String(50), nullable=True)
    custom_instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    resume_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("resumes.id"), nullable=True)
    job_description_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("job_descriptions.id"), nullable=True
    )
    template_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("interview_templates.id"), nullable=True
    )
    configuration_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("interview_configurations.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    timer_remaining: Mapped[int] = mapped_column(Integer, default=1800)
    transcript: Mapped[list] = mapped_column(JSONB, default=list)
    ai_messages: Mapped[list] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user = relationship("User", backref="interviews")
    resume = relationship("Resume", back_populates="interviews", foreign_keys=[resume_id])
    job_description = relationship("JobDescription", back_populates="interviews", foreign_keys=[job_description_id])
    template = relationship("InterviewTemplate", back_populates="interviews", foreign_keys=[template_id])
    configuration = relationship("InterviewConfiguration", back_populates="interview", foreign_keys=[configuration_id])
    evaluation = relationship("Evaluation", back_populates="interview", uselist=False)


class InterviewConfiguration(Base):
    """Structured configuration snapshot from the Setup wizard.

    Stored alongside the interview as a denormalised snapshot so that
    even if the schema changes in the future, the exact configuration
    used for this interview is preserved.
    """

    __tablename__ = "interview_configurations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    interview_type: Mapped[str] = mapped_column(String(20), nullable=False)
    company: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    experience_level: Mapped[str] = mapped_column(String(20), nullable=False)
    language: Mapped[str | None] = mapped_column(String(20), nullable=True)
    spoken_language: Mapped[str | None] = mapped_column(String(10), nullable=True, default="en")
    framework: Mapped[str | None] = mapped_column(String(50), nullable=True)
    difficulty: Mapped[str] = mapped_column(String(10), nullable=False, default="medium")
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    custom_instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    device_checks: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    interview = relationship("Interview", back_populates="configuration", foreign_keys=[Interview.configuration_id])


class Resume(Base):
    """Uploaded resume metadata and (optionally) parsed content."""

    __tablename__ = "resumes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    parsed_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    interviews = relationship("Interview", back_populates="resume", foreign_keys=[Interview.resume_id])


class JobDescription(Base):
    """Uploaded job-description metadata and parsed text."""

    __tablename__ = "job_descriptions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    storage_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False, default="", index=True)
    raw_content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    parsed_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="text")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    interviews = relationship(
        "Interview",
        back_populates="job_description",
        foreign_keys=[Interview.job_description_id],
    )


class InterviewTemplate(Base):
    """Pre-configured interview presets (e.g. ``FAANG Frontend Coding``).

    Templates populate the setup wizard with sensible defaults.  Admins
    can create templates; regular users can fork them into a custom setup.
    """

    __tablename__ = "interview_templates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    interview_type: Mapped[str] = mapped_column(String(20), nullable=False)
    default_company: Mapped[str | None] = mapped_column(String(100), nullable=True)
    default_role: Mapped[str | None] = mapped_column(String(100), nullable=True)
    default_experience_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    default_language: Mapped[str | None] = mapped_column(String(20), nullable=True)
    default_framework: Mapped[str | None] = mapped_column(String(50), nullable=True)
    default_difficulty: Mapped[str] = mapped_column(String(10), nullable=False, default="medium")
    default_duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    default_instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    interviews = relationship("Interview", back_populates="template", foreign_keys=[Interview.template_id])


class UserTemplate(Base):
    """User-saved interview configuration templates.

    Unlike admin InterviewTemplates (which provide defaults), UserTemplate
    stores an exact configuration snapshot that the user can one-click load.
    """

    __tablename__ = "user_templates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    interview_type: Mapped[str] = mapped_column(String(20), nullable=False)
    company: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(100), nullable=False)
    experience_level: Mapped[str] = mapped_column(String(20), nullable=False)
    language: Mapped[str | None] = mapped_column(String(20), nullable=True)
    framework: Mapped[str | None] = mapped_column(String(50), nullable=True)
    difficulty: Mapped[str] = mapped_column(String(10), nullable=False, default="medium")
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    custom_instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    resume_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("resumes.id"), nullable=True)
    job_description_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("job_descriptions.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)
