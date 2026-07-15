"""Execution logger — structured logging for all code execution events."""

from __future__ import annotations

import logging
import time
from typing import Any

logger = logging.getLogger("execution")


def log_execution(
    submission_id: str,
    language: str,
    status: str,
    execution_ms: int = 0,
    error: str | None = None,
    **extra: Any,
) -> None:
    """Log a structured code execution event."""
    entry = {
        "event": "code.execution",
        "submission_id": submission_id[:8],
        "language": language,
        "status": status,
        "execution_ms": execution_ms,
        "timestamp": time.time(),
    }
    if error:
        entry["error"] = error
    entry.update(extra)
    logger.info("Code execution: %(submission_id)s %(language)s -> %(status)s (%(execution_ms)dms)", entry)
