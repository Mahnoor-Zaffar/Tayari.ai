"""Dashboard response schemas.

Every model follows the project convention of returning ``{"success": True, "data": {...}}``
— these Pydantic models represent the *data* payload only.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class UserProfile(BaseModel):
    """Non-sensitive user information displayed on the dashboard."""

    id: UUID
    email: str
    username: str
    display_name: str
    email_verified: bool
    created_at: datetime


class DashboardStats(BaseModel):
    """Aggregated interview and performance statistics."""

    total_interviews: int = 0
    completed_interviews: int = 0
    active_interviews: int = 0
    average_score: float | None = None
    current_streak: int = 0
    credits_remaining: int = 0


class SubscriptionInfo(BaseModel):
    """Current subscription details surfaced on the dashboard."""

    plan: str | None = None
    status: str | None = None
    current_period_end: datetime | None = None


class LatestReport(BaseModel):
    """Most recent evaluation summary."""

    interview_id: UUID
    overall_score: float | None = None
    hire_verdict: str | None = None
    created_at: datetime | None = None


class DashboardResponse(BaseModel):
    """Top-level dashboard aggregate returned by ``GET /dashboard``."""

    user: UserProfile
    stats: DashboardStats
    subscription: SubscriptionInfo | None = None
    latest_report: LatestReport | None = None


class RecentInterview(BaseModel):
    """Interview summary for the recent activity list."""

    id: UUID
    type: str
    company: str
    status: str
    overall_score: float | None = None
    completed_at: datetime | None = None
    created_at: datetime


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
