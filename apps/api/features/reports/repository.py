"""Evaluation data access layer."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from evaluation.types import EvaluationResult, DimensionScore
from features.reports.models import Evaluation


class EvaluationRepository:
    """Async repository for evaluation persistence."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_user_evaluations(self, user_id: UUID, limit: int = 50) -> list[dict]:
        from features.interview.models import Interview
        result = await self._session.execute(
            select(Evaluation).join(Interview, Evaluation.interview_id == Interview.id)
            .where(Interview.user_id == user_id, Evaluation.deleted_at.is_(None))
            .order_by(Evaluation.created_at.desc()).limit(limit)
        )
        evals = list(result.scalars().all())
        return [
            {
                "id": str(e.id),
                "interview_id": str(e.interview_id),
                "overall_score": e.overall_score,
                "hire_verdict": e.hire_verdict,
                "dimensions": e.dimension_scores,
                "strengths": e.strengths,
                "improvements": e.improvements,
                "status": e.status,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in evals
        ]

    async def create_evaluation(self, result: EvaluationResult) -> Evaluation:
        """Persist a validated EvaluationResult to the database.

        This is the **only** path for writing evaluation data.
        The LLM never writes directly to the database.
        """
        evaluation = Evaluation(
            interview_id=UUID(result.interview_id),
            overall_score=result.overall_score,
            dimension_scores={d.key: {"score": d.score, "evidence": d.evidence} for d in result.dimensions},
            hire_verdict=result.hire_verdict,
            strengths=result.strengths,
            improvements=result.improvements,
            delta_vs_last=None,
            raw_evaluation=result.raw_evaluation,
            model_used=result.model_used,
            status="completed",
        )
        self._session.add(evaluation)
        await self._session.flush()
        await self._session.refresh(evaluation)
        return evaluation

    async def get_evaluation(self, interview_id: UUID) -> Evaluation | None:
        result = await self._session.execute(
            select(Evaluation).where(Evaluation.interview_id == interview_id)
        )
        return result.scalar_one_or_none()

    async def get_user_evaluations(self, user_id: UUID, limit: int = 20) -> list[Evaluation]:
        from features.interview.models import Interview
        result = await self._session.execute(
            select(Evaluation).join(Interview).where(
                Interview.user_id == user_id,
                Evaluation.deleted_at.is_(None),
            ).order_by(Evaluation.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())
