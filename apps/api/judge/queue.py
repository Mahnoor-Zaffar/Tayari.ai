"""Execution Queue — async job processing for code submissions.

Manages a FIFO queue of execution jobs with concurrency limits,
priority support, and backpressure handling.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum

from judge.sandbox import Sandbox, SandboxResult

logger = logging.getLogger(__name__)


class JobPriority(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2


class JobStatus(Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ExecutionJob:
    """A single code execution job in the queue."""

    id: str
    language: str
    source_code: str
    test_input: str
    priority: JobPriority = JobPriority.NORMAL
    status: JobStatus = JobStatus.QUEUED
    created_at: float = field(default_factory=time.time)
    started_at: float | None = None
    completed_at: float | None = None
    result: SandboxResult | None = None
    error: str | None = None


class ExecutionQueue:
    """Async FIFO queue with concurrency cap and priority.

    Limit concurrent executions to prevent resource exhaustion.
    Supports cancellation and status polling.
    """

    def __init__(self, max_concurrent: int = 5) -> None:
        self._max_concurrent = max_concurrent
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._jobs: dict[str, ExecutionJob] = {}
        self._queue: asyncio.Queue[ExecutionJob] = asyncio.Queue()
        self._worker_task: asyncio.Task | None = None
        self._running = False

    def enqueue(self, job: ExecutionJob) -> None:
        """Add a job to the execution queue."""
        self._jobs[job.id] = job
        self._queue.put_nowait(job)
        logger.debug("Job queued: %s (%s)", job.id[:8], job.language)

    def get_job(self, job_id: str) -> ExecutionJob | None:
        return self._jobs.get(job_id)

    def cancel_job(self, job_id: str) -> bool:
        job = self._jobs.get(job_id)
        if job and job.status == JobStatus.QUEUED:
            job.status = JobStatus.CANCELLED
            return True
        return False

    @property
    def pending_count(self) -> int:
        return self._queue.qsize()

    @property
    def active_count(self) -> int:
        return sum(1 for j in self._jobs.values() if j.status == JobStatus.RUNNING)

    async def start(self) -> None:
        """Start the background worker that processes queued jobs."""
        if self._running:
            return
        self._running = True
        self._worker_task = asyncio.create_task(self._worker_loop())

    async def stop(self) -> None:
        """Stop the background worker."""
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass

    async def _worker_loop(self) -> None:
        """Continuously dequeue and execute jobs up to max_concurrent."""
        while self._running:
            try:
                job = await asyncio.wait_for(self._queue.get(), timeout=1.0)
            except TimeoutError:
                continue

            if job.status == JobStatus.CANCELLED:
                continue

            async with self._semaphore:
                job.status = JobStatus.RUNNING
                job.started_at = time.time()
                try:
                    result = await Sandbox.run(
                        source_code=job.source_code,
                        language=job.language,
                        test_input=job.test_input,
                    )
                    job.result = result
                    job.status = JobStatus.COMPLETED
                except Exception as exc:
                    job.status = JobStatus.FAILED
                    job.error = str(exc)
                finally:
                    job.completed_at = time.time()
                    self._queue.task_done()
