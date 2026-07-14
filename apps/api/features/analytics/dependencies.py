"""Analytics dependency injection."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from features.analytics.repository import AnalyticsRepository
from features.analytics.service import AnalyticsService


async def get_analytics_service(
    db: AsyncSession = Depends(get_db),
) -> AnalyticsService:
    """FastAPI dependency that returns an ``AnalyticsService`` instance."""
    repository = AnalyticsRepository(db)
    return AnalyticsService(repository)
