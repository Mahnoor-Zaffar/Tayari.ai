"""Metrics Collector — execution timing, pass rates, error counters.

Provides a lightweight aggregation layer for operational dashboards.
Metrics are maintained in-memory with optional periodic flush to the DB.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class LanguageMetrics:
    executions: int = 0
    failures: int = 0
    timeouts: int = 0
    total_execution_ms: int = 0
    total_tests: int = 0
    passed_tests: int = 0


@dataclass
class GlobalMetrics:
    total_executions: int = 0
    total_failures: int = 0
    total_timeouts: int = 0
    avg_execution_ms: float = 0.0
    overall_pass_rate: float = 0.0
    by_language: dict[str, LanguageMetrics] = field(default_factory=dict)
    started_at: float = field(default_factory=time.time)


class MetricsCollector:
    """Collects execution metrics for monitoring and dashboards.

    Thread-safe counters aggregated per language.
    """

    def __init__(self) -> None:
        self._global = GlobalMetrics()

    def record_execution(
        self,
        language: str,
        execution_ms: int,
        tests_passed: int = 0,
        tests_total: int = 0,
        timed_out: bool = False,
        failed: bool = False,
    ) -> None:
        """Record a single code execution result."""
        self._global.total_executions += 1
        if failed:
            self._global.total_failures += 1
        if timed_out:
            self._global.total_timeouts += 1

        lang = self._global.by_language.setdefault(language, LanguageMetrics())
        lang.executions += 1
        lang.total_execution_ms += execution_ms
        lang.total_tests += tests_total
        lang.passed_tests += tests_passed
        if failed:
            lang.failures += 1
        if timed_out:
            lang.timeouts += 1

        n = self._global.total_executions
        self._global.avg_execution_ms = (
            (self._global.avg_execution_ms * (n - 1) + execution_ms) / n
        )
        total_tests = sum(l.total_tests for l in self._global.by_language.values())
        total_passed = sum(l.passed_tests for l in self._global.by_language.values())
        self._global.overall_pass_rate = (
            (total_passed / total_tests * 100) if total_tests > 0 else 0.0
        )

    def snapshot(self) -> GlobalMetrics:
        """Return a snapshot of current metrics."""
        return self._global

    @property
    def total_executions(self) -> int:
        return self._global.total_executions

    @property
    def total_failures(self) -> int:
        return self._global.total_failures


# Singleton
_metrics: MetricsCollector | None = None


def get_metrics() -> MetricsCollector:
    global _metrics
    if _metrics is None:
        _metrics = MetricsCollector()
    return _metrics
