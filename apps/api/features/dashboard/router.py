"""Dashboard API routes.

Three read-only endpoints:
- ``GET /dashboard``         → full dashboard aggregate
- ``GET /dashboard/recent``   → recent interview activity
- ``GET /dashboard/analytics`` → daily / weekly / monthly time-series
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from core.errors import success_response
from features.auth.guard import CurrentUser, get_current_user
from features.dashboard.dependencies import get_dashboard_service
from features.dashboard.service import DashboardService

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
    "/dashboard/analytics",
    summary="Interview activity time-series",
    description="Returns daily, weekly, and monthly interview counts and average scores.",
)
async def get_analytics(
    current_user: CurrentUser = Depends(get_current_user),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
) -> dict:
    """Return time-series activity data for the authenticated user."""
    data = await dashboard_service.get_analytics(current_user.id)
    return success_response(data.model_dump())
