"""Interview data-access layer.

Each method is a single well-scoped query or write.  Returns plain dicts
or ORM instances — the service layer converts to Pydantic models.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from features.interview.models import (
    Interview as InterviewORM,
)
from features.interview.models import (
    InterviewConfiguration,
    InterviewTemplate,
    JobDescription,
    Resume,
)


def _now() -> datetime:
    return datetime.now(UTC)


class InterviewRepository:
    """Async repository for interview-related database operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── Interview CRUD ───────────────────────────────────────────────────

    async def create_interview(self, data: dict[str, Any]) -> InterviewORM:
        """Insert a new interview row and return the ORM instance."""
        interview = InterviewORM(**data)
        self._session.add(interview)
        await self._session.flush()
        await self._session.refresh(interview)
        return interview

    async def get_interview_by_id(self, interview_id: UUID, user_id: UUID) -> InterviewORM | None:
        """Fetch a single interview by ID, scoped to the user."""
        result = await self._session.execute(
            select(InterviewORM).where(
                InterviewORM.id == interview_id,
                InterviewORM.user_id == user_id,
                InterviewORM.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def list_interviews(self, user_id: UUID, limit: int = 20, offset: int = 0) -> list[InterviewORM]:
        """Return paginated interviews for a user, newest first."""
        result = await self._session.execute(
            select(InterviewORM)
            .where(
                InterviewORM.user_id == user_id,
                InterviewORM.deleted_at.is_(None),
            )
            .order_by(InterviewORM.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def count_user_interviews(self, user_id: UUID) -> int:
        """Count non-deleted interviews for eligibility checks."""
        result = await self._session.execute(
            select(InterviewORM.id).where(
                InterviewORM.user_id == user_id,
                InterviewORM.deleted_at.is_(None),
            )
        )
        return len(list(result.scalars().all()))

    async def soft_delete(self, interview_id: UUID) -> bool:
        """Soft-delete an interview by setting ``deleted_at``."""
        interview = await self._session.get(InterviewORM, interview_id)
        if interview is None:
            return False
        interview.deleted_at = _now()
        await self._session.flush()
        return True

    # ── Configuration ─────────────────────────────────────────────────────

    async def create_configuration(self, data: dict[str, Any]) -> InterviewConfiguration:
        """Persist the wizard configuration snapshot."""
        config = InterviewConfiguration(**data)
        self._session.add(config)
        await self._session.flush()
        await self._session.refresh(config)
        return config

    # ── Resume ────────────────────────────────────────────────────────────

    async def find_resume_by_hash(self, user_id: UUID, file_hash: str) -> Resume | None:
        """Find an existing resume by content hash (de-duplication)."""
        result = await self._session.execute(
            select(Resume).where(
                Resume.user_id == user_id,
                Resume.file_hash == file_hash,
            )
        )
        return result.scalar_one_or_none()

    async def create_resume(self, data: dict[str, Any]) -> Resume:
        """Insert resume metadata row."""
        resume = Resume(**data)
        self._session.add(resume)
        await self._session.flush()
        await self._session.refresh(resume)
        return resume

    async def get_resume_by_id(self, resume_id: UUID, user_id: UUID) -> Resume | None:
        """Fetch a resume, scoped to the user."""
        result = await self._session.execute(
            select(Resume).where(
                Resume.id == resume_id,
                Resume.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    # ── Job Description ────────────────────────────────────────────────────

    async def find_job_description_by_hash(self, user_id: UUID, file_hash: str) -> JobDescription | None:
        """Find an existing JD by content hash (de-duplication)."""
        if not file_hash:
            return None
        result = await self._session.execute(
            select(JobDescription).where(
                JobDescription.user_id == user_id,
                JobDescription.file_hash == file_hash,
            )
        )
        return result.scalar_one_or_none()

    async def create_job_description(self, data: dict[str, Any]) -> JobDescription:
        """Insert JD metadata row."""
        jd = JobDescription(**data)
        self._session.add(jd)
        await self._session.flush()
        await self._session.refresh(jd)
        return jd

    async def get_job_description_by_id(self, jd_id: UUID, user_id: UUID) -> JobDescription | None:
        """Fetch a JD, scoped to the user."""
        result = await self._session.execute(
            select(JobDescription).where(
                JobDescription.id == jd_id,
                JobDescription.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    # ── Templates ─────────────────────────────────────────────────────────

    async def list_active_templates(self) -> list[InterviewTemplate]:
        """Return all active interview templates."""
        result = await self._session.execute(
            select(InterviewTemplate).where(InterviewTemplate.is_active.is_(True)).order_by(InterviewTemplate.name)
        )
        return list(result.scalars().all())
