"""Analytics orchestration layer.

Aggregates completed-interview activity into daily, weekly, and monthly
time-series buckets.  The repository returns data in ascending order and
the service buckets in Python, avoiding dialect-specific SQL functions.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from features.analytics.repository import AnalyticsRepository
from features.analytics.schemas import AnalyticsDatapoint, AnalyticsResponse


class AnalyticsService:
    """Stateless service that produces time-series analytics."""

    def __init__(self, repository: AnalyticsRepository) -> None:
        self._repository = repository

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
