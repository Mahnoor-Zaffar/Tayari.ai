"""Analytics data-access layer.

Provides time-series data for interview activity.  This repository queries
the shared database directly rather than going through other feature services,
keeping the analytics module self-contained.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from features.interview.models import Interview as InterviewORM
from features.reports.models import Evaluation as EvaluationORM


class AnalyticsRepository:
    """Read-only repository for interview activity time-series."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_analytics_data(self, user_id: UUID, since_days: int = 365) -> list[dict[str, Any]]:
        """Return completed interviews with scores for time-series aggregation.

        Results are ordered ascending so the service layer can iterate once
        for all three groupings (daily / weekly / monthly).
        """
        cutoff = datetime.now(UTC) - timedelta(days=since_days)

        rows = (
            await self._session.execute(
                select(
                    InterviewORM.completed_at,
                    EvaluationORM.overall_score,
                )
                .outerjoin(
                    EvaluationORM,
                    EvaluationORM.interview_id == InterviewORM.id,
                )
                .where(
                    InterviewORM.user_id == user_id,
                    InterviewORM.status == "completed",
                    InterviewORM.completed_at.isnot(None),
                    InterviewORM.completed_at >= cutoff,
                    InterviewORM.deleted_at.is_(None),
                    EvaluationORM.deleted_at.is_(None),
                )
                .order_by(InterviewORM.completed_at.asc())
            )
        ).all()

        return [
            {
                "completed_at": row.completed_at,
                "overall_score": float(row.overall_score) if row.overall_score is not None else None,
            }
            for row in rows
        ]
