"""Analytics response schemas.

Every model follows the project convention of returning ``{"success": True, "data": {...}}``
— these Pydantic models represent the *data* payload only.
"""

from pydantic import BaseModel


class AnalyticsDatapoint(BaseModel):
    """Single time-series data point."""

    period: str
    interviews: int
    average_score: float | None = None


class AnalyticsResponse(BaseModel):
    """Time-series activity broken down by daily, weekly, and monthly windows."""

    daily: list[AnalyticsDatapoint]
    weekly: list[AnalyticsDatapoint]
    monthly: list[AnalyticsDatapoint]
