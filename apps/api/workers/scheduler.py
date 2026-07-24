"""APScheduler integration for background job processing.

Provides a singleton ``AsyncIOScheduler`` with a PostgreSQL-backed job
store so that scheduled evaluations survive server restarts.

Usage:
    from workers.scheduler import scheduler, schedule_evaluation

    # On app startup
    await scheduler.start()

    # When a session completes
    await schedule_evaluation(interview_id, user_id)

    # On app shutdown
    scheduler.shutdown()
"""

from __future__ import annotations

import logging

from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from core.config import settings

logger = logging.getLogger(__name__)

# Build a sync PostgreSQL URL from the async DATABASE_URL
_SYNC_DB_URL = settings.DATABASE_URL.replace("+asyncpg", "")

# ── Job stores ────────────────────────────────────────────────────────────────

jobstores = {
    "default": SQLAlchemyJobStore(url=_SYNC_DB_URL),
}

# ── Executors ─────────────────────────────────────────────────────────────────

executors = {
    "default": AsyncIOExecutor(),
}

# ── Job defaults ──────────────────────────────────────────────────────────────

job_defaults = {
    "coalesce": True,  # Merge multiple pending runs into one
    "max_instances": 3,  # Allow up to 3 concurrent evaluation runs
    "misfire_grace_time": 300,  # Allow job to run up to 5 min late
}

# ── Singleton scheduler ───────────────────────────────────────────────────────

scheduler = AsyncIOScheduler(
    jobstores=jobstores,
    executors=executors,
    job_defaults=job_defaults,
)


async def schedule_evaluation(interview_id: str, user_id: str) -> None:
    """Schedule an interview evaluation as a background APScheduler job.

    The job is persisted in PostgreSQL so it survives server restarts.
    If a job for the same interview already exists it will be replaced.
    """
    job_id = f"evaluate_{interview_id}"

    # Remove any previous job for this interview (e.g. from a prior attempt)
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)

    scheduler.add_job(
        "workers.evaluation:generate_evaluation",
        kwargs={"interview_id": interview_id, "user_id": user_id},
        id=job_id,
        name=f"Evaluate interview {interview_id[:8]}",
        replace_existing=True,
    )

    logger.info("Scheduled evaluation job %s for interview %s", job_id, interview_id[:8])
