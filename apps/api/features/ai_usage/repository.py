"""AI usage telemetry repository — admin queries over the ai_usage table."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ai.usage.models import AIUsage


@dataclass
class UsageSummary:
    total_calls: int
    error_count: int
    avg_latency_ms: float
    total_token_estimate: int
    total_cost_cents: float
    models_used: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_calls": self.total_calls,
            "error_count": self.error_count,
            "error_rate": round(self.error_count / max(self.total_calls, 1), 4),
            "avg_latency_ms": round(self.avg_latency_ms, 1),
            "total_token_estimate": self.total_token_estimate,
            "total_cost_cents": self.total_cost_cents,
            "models_used": self.models_used,
        }


class UsageRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_records(
        self,
        *,
        task: str | None = None,
        model: str | None = None,
        is_error: bool | None = None,
        since: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AIUsage]:
        stmt = select(AIUsage).order_by(AIUsage.created_at.desc()).limit(limit).offset(offset)
        if task:
            stmt = stmt.where(AIUsage.task == task)
        if model:
            stmt = stmt.where(AIUsage.model == model)
        if is_error is not None:
            stmt = stmt.where(AIUsage.is_error.is_(is_error))
        if since:
            stmt = stmt.where(AIUsage.created_at >= since)
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def summary(
        self,
        *,
        task: str | None = None,
        model: str | None = None,
        since: datetime | None = None,
    ) -> UsageSummary:
        base = select(AIUsage)
        if task:
            base = base.where(AIUsage.task == task)
        if model:
            base = base.where(AIUsage.model == model)
        if since:
            base = base.where(AIUsage.created_at >= since)

        stats = await self._db.execute(
            select(
                func.count(AIUsage.id),
                func.count(AIUsage.id).filter(AIUsage.is_error.is_(True)),
                func.avg(AIUsage.latency_ms),
                func.sum(func.coalesce(AIUsage.prompt_tokens, 0) + func.coalesce(AIUsage.completion_tokens, 0)),
                func.sum(func.coalesce(AIUsage.estimated_cost_cents, 0)),
            ).select_from(base.subquery())
        )
        total_calls, error_count, avg_latency, total_tokens, total_cost = stats.one()

        models_result = await self._db.execute(select(AIUsage.model).where(AIUsage.model.isnot(None)).distinct())
        if model:
            models_used = [model]
        else:
            models_used = list(models_result.scalars().all())

        return UsageSummary(
            total_calls=total_calls or 0,
            error_count=error_count or 0,
            avg_latency_ms=avg_latency or 0.0,
            total_token_estimate=total_tokens or 0,
            total_cost_cents=total_cost or 0.0,
            models_used=models_used,
        )

    def to_dict(self, record: AIUsage) -> dict[str, Any]:
        return {
            "id": str(record.id),
            "task": record.task,
            "provider": record.provider,
            "model": record.model,
            "prompt_version": record.prompt_version,
            "prompt_tokens": record.prompt_tokens,
            "completion_tokens": record.completion_tokens,
            "latency_ms": record.latency_ms,
            "estimated_cost_cents": record.estimated_cost_cents,
            "is_error": record.is_error,
            "error_message": record.error_message,
            "created_at": record.created_at.isoformat() if record.created_at else None,
        }


def default_since(days: int) -> datetime:
    return datetime.now(UTC) - timedelta(days=days)
