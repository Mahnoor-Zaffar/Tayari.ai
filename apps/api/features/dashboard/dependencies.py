"""Dashboard dependency injection.

Follows the same pattern as ``features/auth/dependencies.py``:
request-scoped repository wired into a service singleton.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from features.dashboard.repository import DashboardRepository
from features.dashboard.service import DashboardService


async def get_dashboard_service(
    db: AsyncSession = Depends(get_db),
) -> DashboardService:
    """FastAPI dependency that returns a ``DashboardService`` instance.

    The repository is created per-request (bound to the DB session),
    while the service itself is stateless and could be a singleton.
    Following the existing auth pattern for consistency.
    """
    repository = DashboardRepository(db)
    return DashboardService(repository)
