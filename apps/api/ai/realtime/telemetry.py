"""Performance telemetry for the interview runtime.

Context managers and decorators for measuring latencies
across the AI pipeline, transcript processing, and WebSocket events.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class TelemetrySnapshot:
    """Snapshot of performance metrics for a single session turn."""

    ai_latency_ms: float = 0.0
    transcript_latency_ms: float = 0.0
    total_turn_ms: float = 0.0
    question_count: int = 0
    token_count: int = 0


class PerformanceTelemetry:
    """Collects and exposes performance metrics for the interview runtime.

    Metrics can be consumed by:
    - Operational dashboard (via Prometheus or HTTP endpoint)
    - AI cost tracking
    - Latency alerting
    """

    def __init__(self) -> None:
        self._snapshots: dict[str, list[TelemetrySnapshot]] = {}
        self._session_timing: dict[str, float] = {}

    def session_started(self, session_id: str) -> None:
        self._snapshots[session_id] = []
        self._session_timing[session_id] = time.time()

    def session_ended(self, session_id: str) -> dict[str, Any]:
        started = self._session_timing.pop(session_id, time.time())
        snapshots = self._snapshots.pop(session_id, [])
        total_duration_s = time.time() - started
        avg_ai_latency = sum(s.ai_latency_ms for s in snapshots) / max(len(snapshots), 1)
        return {
            "total_duration_s": round(total_duration_s, 1),
            "total_turns": len(snapshots),
            "avg_ai_latency_ms": round(avg_ai_latency, 1),
            "max_ai_latency_ms": round(max((s.ai_latency_ms for s in snapshots), default=0), 1),
            "snapshots": snapshots,
        }

    def record_turn(self, session_id: str, snapshot: TelemetrySnapshot) -> None:
        if session_id not in self._snapshots:
            self._snapshots[session_id] = []
        self._snapshots[session_id].append(snapshot)

    def get_session_metrics(self, session_id: str) -> dict[str, Any] | None:
        snapshots = self._snapshots.get(session_id)
        if not snapshots:
            return None
        return {
            "turns": len(snapshots),
            "avg_ai_latency_ms": round(sum(s.ai_latency_ms for s in snapshots) / len(snapshots), 1),
        }


@contextmanager
def measure_timer(label: str) -> Callable[[], float]:
    """Context manager that measures elapsed time.

    Usage:
        with measure_timer("ai.chat") as elapsed:
            await provider.chat(...)
        logger.info("chat took %0.0fms", elapsed())
    """
    start = time.time()
    results: list[float] = []

    def elapsed() -> float:
        return (time.time() - start) * 1000

    try:
        yield elapsed
    finally:
        results.append((time.time() - start) * 1000)
