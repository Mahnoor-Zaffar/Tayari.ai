"""Evaluation service — orchestrates the evaluation pipeline for interviews."""

from __future__ import annotations

import logging
from uuid import UUID

from ai.openai_provider import OpenAIProvider
from evaluation.pipeline import EvaluationPipeline
from evaluation.recommendations import RecommendationService
from features.code.repository import CodeRepository
from features.interview.repository import InterviewRepository
from features.reports.repository import EvaluationRepository

logger = logging.getLogger(__name__)


class EvaluationService:
    """Application service for interview evaluations.

    Triggers the evaluation pipeline for completed interviews.
    """

    def __init__(
        self,
        eval_repo: EvaluationRepository,
        interview_repo: InterviewRepository,
        code_repo: CodeRepository | None = None,
        pipeline: EvaluationPipeline | None = None,
    ) -> None:
        self._eval_repo = eval_repo
        self._interview_repo = interview_repo
        self._code_repo = code_repo
        self._pipeline = pipeline or EvaluationPipeline(provider=OpenAIProvider())
        self._recommendations = RecommendationService()

    async def evaluate_interview(self, interview_id: UUID, user_id: UUID) -> dict:
        """Run the full evaluation pipeline for an interview.

        Collects all data, runs the pipeline, persists results.
        """
        interview = await self._interview_repo.get_interview_by_id(interview_id, user_id)
        if interview is None:
            raise ValueError("Interview not found")

        transcript = interview.transcript or []

        result = await self._pipeline.evaluate(
            interview_id=str(interview_id),
            interview_type=interview.type,
            company=interview.company,
            role=interview.role,
            experience_level=interview.experience_level,
            transcript=transcript,
            language=interview.language or "",
        )

        recommendations = self._recommendations.generate(result)
        result.recommendations = recommendations

        evaluation = await self._eval_repo.create_evaluation(result)

        return {
            "evaluation_id": str(evaluation.id),
            "interview_id": str(interview_id),
            "overall_score": result.overall_score,
            "overall_score_100": result.overall_score_100,
            "hire_verdict": result.hire_verdict,
            "dimensions": [
                {"key": d.key, "label": d.label, "score": d.score, "evidence": d.evidence}
                for d in result.dimensions
            ],
            "strengths": result.strengths,
            "improvements": result.improvements,
            "recommendations": recommendations,
            "confidence": result.confidence,
        }

    async def get_evaluation(self, interview_id: UUID) -> dict | None:
        evaluation = await self._eval_repo.get_evaluation(interview_id)
        if evaluation is None:
            return None
        return {
            "id": str(evaluation.id),
            "interview_id": str(evaluation.interview_id),
            "overall_score": evaluation.overall_score,
            "hire_verdict": evaluation.hire_verdict,
            "dimensions": evaluation.dimension_scores,
            "strengths": evaluation.strengths,
            "improvements": evaluation.improvements,
            "status": evaluation.status,
            "created_at": evaluation.created_at.isoformat() if evaluation.created_at else None,
        }
