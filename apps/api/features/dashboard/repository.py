"""Dashboard data-access layer.

Aggregates read-only data from ``interviews``, ``evaluations``, and
``subscriptions`` tables.  Each method is a single well-scoped query —
the caller (``DashboardService``) composes them into the final response.

No cross-feature service calls are made; this repository imports ORM models
directly (acceptable in a modular monolith for read-only aggregation).
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from features.billing.models import Subscription as SubscriptionORM
from features.interview.models import Interview as InterviewORM
from features.reports.models import Evaluation as EvaluationORM


def _utc_today() -> date:
    return datetime.now(UTC).date()


class DashboardRepository:
    """Read-only repository that aggregates dashboard data across tables.

    Every method accepts a ``user_id`` parameter and returns plain Python
    objects (dicts, tuples, scalars) — never ORM instances.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── User profile ─────────────────────────────────────────────────────────

    async def get_user_profile(self, user_id: UUID) -> dict[str, Any]:
        """Return non-sensitive user fields for the dashboard."""
        from features.auth.models import User as UserORM

        row = (
            await self._session.execute(
                select(
                    UserORM.id,
                    UserORM.email,
                    UserORM.username,
                    UserORM.display_name,
                    UserORM.email_verified,
                    UserORM.created_at,
                ).where(UserORM.id == user_id)
            )
        ).first()

        if row is None:
            return {}

        return {
            "id": row.id,
            "email": row.email,
            "username": row.username,
            "display_name": row.display_name,
            "email_verified": row.email_verified,
            "created_at": row.created_at,
        }

    # ── Stats ────────────────────────────────────────────────────────────────

    async def get_stats(self, user_id: UUID) -> dict[str, Any]:
        """Return aggregate interview counts and overall average score."""
        row = (
            await self._session.execute(
                select(
                    func.count(InterviewORM.id).label("total"),
                    func.sum(case((InterviewORM.status == "completed", 1), else_=0)).label("completed"),
                    func.sum(case((InterviewORM.status.in_(["pending", "in_progress"]), 1), else_=0)).label(
                        "active_pending"
                    ),
                    func.avg(EvaluationORM.overall_score).label("avg_score"),
                )
                .outerjoin(
                    EvaluationORM,
                    EvaluationORM.interview_id == InterviewORM.id,
                )
                .where(
                    InterviewORM.user_id == user_id,
                    InterviewORM.deleted_at.is_(None),
                )
            )
        ).one()

        total = row.total or 0
        completed = row.completed or 0
        active = row.active_pending or 0

        return {
            "total_interviews": total,
            "completed_interviews": completed,
            "active_interviews": active,
            "average_score": round(float(row.avg_score), 2) if row.avg_score is not None else None,
        }

    # ── Streak ───────────────────────────────────────────────────────────────

    async def get_streak(self, user_id: UUID) -> int:
        """Return consecutive calendar-day streak of completed interviews."""
        rows = (
            (
                await self._session.execute(
                    select(func.date(InterviewORM.completed_at).label("day"))
                    .where(
                        InterviewORM.user_id == user_id,
                        InterviewORM.status == "completed",
                        InterviewORM.completed_at.isnot(None),
                        InterviewORM.deleted_at.is_(None),
                    )
                    .distinct()
                    .order_by(func.date(InterviewORM.completed_at).desc())
                )
            )
            .scalars()
            .all()
        )

        if not rows:
            return 0

        dates: list[date] = [row if isinstance(row, date) else date.fromisoformat(row) for row in rows]

        today = _utc_today()
        if (today - dates[0]).days > 1:
            return 0

        streak = 1
        for i in range(1, len(dates)):
            diff = (dates[i - 1] - dates[i]).days
            if diff == 1:
                streak += 1
            elif diff == 0:
                continue
            else:
                break
        return streak

    # ── Latest report ─────────────────────────────────────────────────────────

    async def get_latest_report(self, user_id: UUID) -> dict[str, Any] | None:
        """Return the most recent evaluation for this user, if any."""
        row = (
            await self._session.execute(
                select(
                    InterviewORM.id.label("interview_id"),
                    EvaluationORM.overall_score,
                    EvaluationORM.hire_verdict,
                    EvaluationORM.created_at,
                )
                .join(
                    EvaluationORM,
                    EvaluationORM.interview_id == InterviewORM.id,
                )
                .where(
                    InterviewORM.user_id == user_id,
                    InterviewORM.deleted_at.is_(None),
                    EvaluationORM.deleted_at.is_(None),
                )
                .order_by(EvaluationORM.created_at.desc())
                .limit(1)
            )
        ).first()

        if row is None:
            return None

        return {
            "interview_id": row.interview_id,
            "overall_score": float(row.overall_score) if row.overall_score is not None else None,
            "hire_verdict": row.hire_verdict,
            "created_at": row.created_at,
        }

    # ── Subscription ─────────────────────────────────────────────────────────

    async def get_subscription(self, user_id: UUID) -> dict[str, Any] | None:
        """Return the user's active subscription, if any."""
        row = (
            await self._session.execute(
                select(
                    SubscriptionORM.plan,
                    SubscriptionORM.status,
                    SubscriptionORM.current_period_end,
                ).where(
                    SubscriptionORM.user_id == user_id,
                    SubscriptionORM.deleted_at.is_(None),
                )
            )
        ).first()

        if row is None or row.plan is None:
            return None

        return {
            "plan": row.plan,
            "status": row.status,
            "current_period_end": row.current_period_end,
        }

    # ── Recent interviews ────────────────────────────────────────────────────

    async def get_recent_interviews(self, user_id: UUID, limit: int = 20) -> list[dict[str, Any]]:
        """Return the most recent interviews with their evaluation score."""
        rows = (
            await self._session.execute(
                select(
                    InterviewORM.id,
                    InterviewORM.type,
                    InterviewORM.company,
                    InterviewORM.status,
                    EvaluationORM.overall_score,
                    InterviewORM.completed_at,
                    InterviewORM.created_at,
                )
                .outerjoin(
                    EvaluationORM,
                    EvaluationORM.interview_id == InterviewORM.id,
                )
                .where(
                    InterviewORM.user_id == user_id,
                    InterviewORM.deleted_at.is_(None),
                )
                .order_by(InterviewORM.created_at.desc())
                .limit(limit)
            )
        ).all()

        return [
            {
                "id": row.id,
                "type": row.type,
                "company": row.company,
                "status": row.status,
                "overall_score": float(row.overall_score) if row.overall_score is not None else None,
                "completed_at": row.completed_at,
                "created_at": row.created_at,
            }
            for row in rows
        ]

    # ── Analytics ────────────────────────────────────────────────────────────

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
