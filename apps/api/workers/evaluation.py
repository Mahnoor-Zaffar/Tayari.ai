"""Background evaluation worker.

Handles post-interview evaluation asynchronously outside the request
cycle.  Creates its own DB session so it can run independently.

Usage:
    from workers.evaluation import generate_evaluation
    await generate_evaluation(interview_id, user_id)
"""

from __future__ import annotations

import logging
from uuid import UUID

from core.database import async_session
from features.interview.repository import InterviewRepository
from features.reports.repository import EvaluationRepository
from features.reports.service import EvaluationService

logger = logging.getLogger(__name__)


async def generate_evaluation(interview_id: str, user_id: str) -> dict | None:
    """Run the evaluation pipeline for a completed interview.

    Creates an independent DB session, loads the interview data,
    runs the AI evaluation pipeline, and persists the result.

    Returns the evaluation dict on success, or ``None`` on failure.
    """
    logger.info("Generating evaluation for interview %s", interview_id[:8])
    try:
        async with async_session() as db:
            eval_repo = EvaluationRepository(db)
            interview_repo = InterviewRepository(db)
            service = EvaluationService(eval_repo=eval_repo, interview_repo=interview_repo)

            result = await service.evaluate_interview(UUID(interview_id), UUID(user_id))

            if db.is_active:
                await db.commit()

            logger.info(
                "Evaluation completed for interview %s — score=%.1f verdict=%s",
                interview_id[:8],
                result.get("overall_score", 0),
                result.get("hire_verdict", "unknown"),
            )
            return result

    except Exception:
        logger.exception("Evaluation failed for interview %s", interview_id[:8])
        return None
