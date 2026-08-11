"""AI usage telemetry — records per-call usage and persists to the database.

The recorder is deliberately decoupled from the request path: the model
gateway calls ``record_sync`` (a fast, non-blocking in-memory append), and a
background flush loop (started in ``main.lifespan``) drains the buffer to the
``ai_usage`` table in batches.
"""

from __future__ import annotations

import logging
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any

from core.config import settings
from core.database import async_session

logger = logging.getLogger(__name__)

MAX_BUFFER_SIZE = 5000

# USD per 1M tokens. Keyed by exact model string, with sensible fallbacks.
_MODEL_RATES: dict[str, tuple[float, float]] = {
    "gpt-4o-mini": (0.15, 0.60),
    "openai/gpt-4o-mini": (0.15, 0.60),
    "gpt-4o": (2.50, 10.00),
    "openai/gpt-4o": (2.50, 10.00),
}

# Prompt versions known to be in production; used as the default tag.
DEFAULT_PROMPT_VERSION = "v1"


def estimate_cost_cents(
    model: str,
    prompt_tokens: int | None,
    completion_tokens: int | None,
) -> float:
    """Estimate cost in cents from token usage and model rates."""
    if not prompt_tokens:
        return 0.0
    in_rate, out_rate = _MODEL_RATES.get(model, (0.30, 1.20))
    cost_usd = (prompt_tokens / 1_000_000) * in_rate + (completion_tokens or 0) / 1_000_000 * out_rate
    return round(cost_usd * 100, 3)


@dataclass
class UsageRecord:
    task: str
    provider: str
    model: str
    created_at: float = field(default_factory=time.time)
    prompt_version: str = DEFAULT_PROMPT_VERSION
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    latency_ms: float | None = None
    is_error: bool = False
    error_message: str | None = None
    interview_id: str | None = None
    session_id: str | None = None
    estimated_cost_cents: float | None = None

    def to_db_payload(self) -> dict[str, Any]:
        from ai.usage.models import ai_usage_row_from_record

        return ai_usage_row_from_record(self)


class _PendingBuffer:
    """Thread-safe bounded buffer of pending UsageRecord instances."""

    def __init__(self) -> None:
        self._records: deque[UsageRecord] = deque(maxlen=MAX_BUFFER_SIZE)
        self._lock = threading.Lock()

    def append(self, record: UsageRecord) -> None:
        with self._lock:
            self._records.append(record)

    def drain(self, n: int | None = None) -> list[UsageRecord]:
        with self._lock:
            if n is None:
                out = list(self._records)
                self._records.clear()
                return out
            out = []
            for _ in range(n):
                if not self._records:
                    break
                out.append(self._records.popleft())
            return out

    def __len__(self) -> int:
        with self._lock:
            return len(self._records)


class UsageRecorder:
    """Buffers AI usage records and flushes them to Postgres in batches."""

    def __init__(self, flush_interval_s: int = 0) -> None:
        self._pending = _PendingBuffer()
        self._flush_interval_s = flush_interval_s or settings.AI_USAGE_FLUSH_INTERVAL_S
        self._flush_task: Any = None  # asyncio.Task, set by lifespan
        self._enabled = settings.AI_USAGE_ENABLED

    # ── recording (non-blocking, call from async code) ──────────────────

    def record_sync(self, record: UsageRecord) -> None:
        if not self._enabled:
            return
        self._pending.append(record)

    # ── flush loop lifecycle ─────────────────────────────────────────────

    async def start_flush_loop(self) -> None:
        import asyncio

        self._flush_task = asyncio.create_task(self._flush_loop())

    async def stop(self) -> None:
        import asyncio

        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except (asyncio.CancelledError, Exception):
                pass
            self._flush_task = None
        await self.flush()

    async def _flush_loop(self) -> None:
        import asyncio

        try:
            while True:
                await asyncio.sleep(self._flush_interval_s)
                await self.flush()
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.exception("AI usage flush loop failed")

    async def flush(self) -> int:
        """Persist all buffered records. Returns the number written."""
        records = self._pending.drain()
        if not records:
            return 0
        try:
            async with async_session() as db:
                from ai.usage.models import AIUsage

                db.add_all([AIUsage(**r.to_db_payload()) for r in records])
                await db.commit()
            logger.info("Flushed %d AI usage records", len(records))
            return len(records)
        except Exception:
            # Never let telemetry failures crash app logic. Drop the batch
            # (records are already drained) and log.
            logger.exception("Failed to persist AI usage records (%d)", len(records))
            return 0


_recorder: UsageRecorder | None = None


def get_usage_recorder() -> UsageRecorder:
    """Return the shared usage recorder singleton."""
    global _recorder
    if _recorder is None:
        _recorder = UsageRecorder()
    return _recorder


def record_usage(
    task: str,
    provider: str,
    model: str,
    *,
    latency_ms: float | None = None,
    prompt_tokens: int | None = None,
    completion_tokens: int | None = None,
    is_error: bool = False,
    error_message: str | None = None,
    prompt_version: str = DEFAULT_PROMPT_VERSION,
) -> None:
    """Convenience wrapper — record a single usage event without blocking."""
    get_usage_recorder().record_sync(
        UsageRecord(
            task=task,
            provider=provider,
            model=model,
            latency_ms=latency_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            is_error=is_error,
            error_message=error_message,
            prompt_version=prompt_version,
            estimated_cost_cents=estimate_cost_cents(model, prompt_tokens, completion_tokens),
        )
    )
