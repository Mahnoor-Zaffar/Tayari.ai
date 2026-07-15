"""Code execution repository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from features.code.models import CodeReview, Submission


class CodeRepository:
    """Async repository for submissions and code reviews."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_submission(self, data: dict) -> Submission:
        submission = Submission(**data)
        self._session.add(submission)
        await self._session.flush()
        await self._session.refresh(submission)
        return submission

    async def get_submission(self, submission_id: UUID, user_id: UUID) -> Submission | None:
        result = await self._session.execute(
            select(Submission).where(
                Submission.id == submission_id,
                Submission.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def update_submission(self, submission_id: UUID, data: dict) -> bool:
        result = await self._session.execute(
            select(Submission).where(Submission.id == submission_id)
        )
        submission = result.scalar_one_or_none()
        if submission is None:
            return False
        for key, value in data.items():
            setattr(submission, key, value)
        await self._session.flush()
        return True

    async def create_code_review(self, data: dict) -> CodeReview:
        review = CodeReview(**data)
        self._session.add(review)
        await self._session.flush()
        await self._session.refresh(review)
        return review

    async def get_code_review(self, submission_id: UUID) -> CodeReview | None:
        result = await self._session.execute(
            select(CodeReview).where(CodeReview.submission_id == submission_id)
        )
        return result.scalar_one_or_none()
