"""AI usage telemetry API routes.

Admin-only read endpoints over model gateway telemetry:
- ``GET /admin/ai-usage`` → recent usage records
- ``GET /admin/ai-usage/summary`` → aggregated stats
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.errors import success_response
from features.ai_usage.repository import UsageRepository, default_since
from features.auth.guard import CurrentUser, RoleChecker

router = APIRouter(tags=["ai-usage"])


@router.get(
    "/admin/ai-usage",
    summary="Recent AI usage records (admin)",
    description="Return the most recent model gateway usage records with optional filters.",
)
async def list_ai_usage(
    _admin: CurrentUser = Depends(RoleChecker("admin")),
    db: AsyncSession = Depends(get_db),
    task: str | None = None,
    model: str | None = None,
    error: bool | None = None,
    days: int = 7,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    repo = UsageRepository(db)
    since = default_since(max(days, 1))
    records = await repo.list_records(
        task=task,
        model=model,
        is_error=error,
        since=since,
        limit=min(max(limit, 1), 200),
        offset=max(offset, 0),
    )
    return success_response(
        {
            "records": [repo.to_dict(r) for r in records],
            "summary": (await repo.summary(task=task, model=model, since=since)).to_dict(),
        }
    )


@router.get(
    "/admin/ai-usage/summary",
    summary="Aggregated AI usage stats (admin)",
    description="Return aggregated model, token, latency, cost, and failure stats.",
)
async def ai_usage_summary(
    _admin: CurrentUser = Depends(RoleChecker("admin")),
    db: AsyncSession = Depends(get_db),
    task: str | None = None,
    model: str | None = None,
    days: int = 7,
) -> dict:
    repo = UsageRepository(db)
    since = default_since(max(days, 1))
    summary = await repo.summary(task=task, model=model, since=since)
    return success_response(summary.to_dict())
