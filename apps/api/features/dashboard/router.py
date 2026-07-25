"""Dashboard API routes.

Two read-only endpoints:
- ``GET /dashboard``         → full dashboard aggregate
- ``GET /dashboard/recent``   → recent interview activity
- ``GET /dashboard/admin``    → system-wide stats (admin only)

Time-series analytics moved to ``features/analytics/`` at ``GET /analytics``.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from core.errors import success_response
from features.auth.guard import CurrentUser, RoleChecker, get_current_user
from features.dashboard.dependencies import get_dashboard_service
from features.dashboard.service import DashboardService
from features.users.dependencies import get_user_service
from features.users.service import UserService

router = APIRouter(tags=["dashboard"])


@router.get(
    "/dashboard",
    summary="Full dashboard aggregate",
    description="Returns user profile, interview statistics, streak, latest report, and subscription info.",
)
async def get_dashboard(
    current_user: CurrentUser = Depends(get_current_user),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
) -> dict:
    """Aggregate all dashboard data for the authenticated user."""
    data = await dashboard_service.get_dashboard(current_user.id)
    return success_response(data.model_dump())


@router.get(
    "/dashboard/recent",
    summary="Recent interview history",
    description="Returns the most recent interviews with evaluation scores.",
)
async def get_recent_interviews(
    current_user: CurrentUser = Depends(get_current_user),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
) -> dict:
    """Return recent interview activity for the authenticated user."""
    data = await dashboard_service.get_recent_interviews(current_user.id)
    return success_response({"interviews": [r.model_dump() for r in data]})


@router.get(
    "/dashboard/admin",
    summary="System-wide stats (admin)",
    description="Returns total users, active/inactive counts for the admin dashboard.",
)
async def get_admin_stats(
    _admin: CurrentUser = Depends(RoleChecker("admin")),
    user_service: UserService = Depends(get_user_service),
) -> dict:
    """Return system-wide stats for the admin dashboard."""
    stats = await user_service.get_stats()
    return success_response(stats)
