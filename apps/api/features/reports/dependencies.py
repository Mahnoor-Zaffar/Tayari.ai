"""Evaluation dependency injection."""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from features.interview.repository import InterviewRepository
from features.reports.repository import EvaluationRepository
from features.reports.service import EvaluationService


async def get_evaluation_service(
    db: AsyncSession = Depends(get_db),
) -> EvaluationService:
    eval_repo = EvaluationRepository(db)
    interview_repo = InterviewRepository(db)
    return EvaluationService(
        eval_repo=eval_repo,
        interview_repo=interview_repo,
    )
