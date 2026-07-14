"""Interview feature dependency injection.

Follows the pattern established by ``features/dashboard/dependencies.py``:
request-scoped repository wired into a stateless service.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from features.interview.repository import InterviewRepository
from features.interview.service import InterviewService


async def get_interview_service(
    db: AsyncSession = Depends(get_db),
) -> InterviewService:
    """FastAPI dependency that returns an ``InterviewService`` instance.

    The repository is created per-request (bound to the DB session),
    while the service itself is stateless.
    """
    repository = InterviewRepository(db)
    return InterviewService(repository)
