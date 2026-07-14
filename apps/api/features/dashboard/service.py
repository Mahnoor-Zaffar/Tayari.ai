"""Dashboard orchestration layer.

Assembles the dashboard response by calling the read-only repository.
Contains zero business logic — only aggregation and formatting.

Design decision: the service never imports or calls services from other
features (interview, billing, reports, etc.).  All cross-table data
access goes through ``DashboardRepository``, which queries the shared
database directly.  This keeps the dashboard decoupled from the
orchestration logic of other features.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from features.dashboard.repository import DashboardRepository
from features.dashboard.schemas import (
    AnalyticsDatapoint,
    AnalyticsResponse,
    DashboardResponse,
    DashboardStats,
    LatestReport,
    RecentInterview,
    SubscriptionInfo,
    UserProfile,
)


class DashboardService:
    """Aggregates read-only data for the dashboard UI.

    Every method delegates to ``DashboardRepository`` and returns
    Pydantic response models — never raw dicts or ORM objects.
    """

    def __init__(self, repository: DashboardRepository) -> None:
        self._repository = repository

    async def get_dashboard(self, user_id: UUID) -> DashboardResponse:
        """Assemble the full dashboard payload.

        Runs several independent queries in sequence (they share the
        same database session).  Each query is a single round-trip,
        so the overhead of executing them separately is negligible
        compared to the benefit of clear, testable methods.
        """
        user_data, stats_data, streak, report_data, sub_data = await self._gather(user_id)

        return DashboardResponse(
            user=UserProfile(**user_data)
            if user_data
            else UserProfile(
                id=user_id, email="", username="", display_name="", email_verified=False, created_at=datetime.now(UTC)
            ),
            stats=DashboardStats(
                **stats_data,
                current_streak=streak,
            ),
            subscription=SubscriptionInfo(**sub_data) if sub_data else None,
            latest_report=LatestReport(**report_data) if report_data else None,
        )

    async def _gather(self, user_id: UUID) -> tuple[dict, dict, int, dict | None, dict | None]:
        """Execute independent repository queries in sequence."""
        user_data = await self._repository.get_user_profile(user_id)
        stats = await self._repository.get_stats(user_id)
        streak = await self._repository.get_streak(user_id)
        latest = await self._repository.get_latest_report(user_id)
        subscription = await self._repository.get_subscription(user_id)
        return user_data, stats, streak, latest, subscription

    async def get_recent_interviews(self, user_id: UUID) -> list[RecentInterview]:
        """Return the most recent interviews with evaluation data."""
        rows = await self._repository.get_recent_interviews(user_id)
        return [RecentInterview(**r) for r in rows]

    async def get_analytics(self, user_id: UUID) -> AnalyticsResponse:
        """Aggregate completed-interview activity into daily, weekly, and
        monthly time-series.

        Data is fetched in a single ascending-order query and bucketed
        in Python.  This avoids dialect-specific ``DATE_TRUNC`` calls
        and keeps the code portable across PostgreSQL, SQLite, etc.
        """
        rows = await self._repository.get_analytics_data(user_id)

        daily: dict[str, list[float | None]] = {}
        weekly: dict[str, list[float | None]] = {}
        monthly: dict[str, list[float | None]] = {}

        for r in rows:
            ts: datetime = r["completed_at"]
            day_key = ts.strftime("%Y-%m-%d")
            week_key = ts.strftime("%G-W%V")  # ISO week
            month_key = ts.strftime("%Y-%m")

            daily.setdefault(day_key, []).append(r["overall_score"])
            weekly.setdefault(week_key, []).append(r["overall_score"])
            monthly.setdefault(month_key, []).append(r["overall_score"])

        return AnalyticsResponse(
            daily=self._to_datapoints(daily),
            weekly=self._to_datapoints(weekly),
            monthly=self._to_datapoints(monthly),
        )

    @staticmethod
    def _to_datapoints(buckets: dict[str, list[float | None]]) -> list[AnalyticsDatapoint]:
        """Convert sorted bucket dict to ordered list of data points."""
        return [
            AnalyticsDatapoint(
                period=key,
                interviews=len(values),
                average_score=(
                    round(
                        sum(s for s in values if s is not None) / len([s for s in values if s is not None]),
                        2,
                    )
                    if any(s is not None for s in values)
                    else None
                ),
            )
            for key, values in sorted(buckets.items())
        ]
