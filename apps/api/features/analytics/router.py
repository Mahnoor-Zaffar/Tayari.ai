"""Analytics API routes.

Single read-only endpoint:
- ``GET /analytics`` → daily / weekly / monthly time-series
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from core.errors import success_response
from features.analytics.dependencies import get_analytics_service
from features.analytics.service import AnalyticsService
from features.auth.guard import CurrentUser, get_current_user

router = APIRouter(tags=["analytics"])


@router.get(
    "/analytics",
    summary="Interview activity time-series",
    description="Returns daily, weekly, and monthly interview counts and average scores.",
)
async def get_analytics(
    current_user: CurrentUser = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> dict:
    """Return time-series activity data for the authenticated user."""
    data = await analytics_service.get_analytics(current_user.id)
    return success_response(data.model_dump())
