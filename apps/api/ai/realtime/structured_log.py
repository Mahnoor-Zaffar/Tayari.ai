"""Structured event logging with correlation IDs.

Provides a context-aware logger that attaches correlation IDs
and structured metadata to every log entry for tracing sessions
across the distributed system.
"""

from __future__ import annotations

import logging
import uuid
from contextvars import ContextVar
from typing import Any

_correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")
_session_id: ContextVar[str] = ContextVar("session_id", default="")


def set_correlation_id(cid: str | None = None) -> str:
    """Set a correlation ID for the current async context.

    Returns the new correlation ID.
    """
    cid = cid or str(uuid.uuid4())[:12]
    _correlation_id.set(cid)
    return cid


def get_correlation_id() -> str:
    return _correlation_id.get()


def set_session_context(session_id: str) -> None:
    _session_id.set(session_id)


def get_session_context() -> str:
    return _session_id.get()


class StructuredLogger:
    """Logger that adds correlation_id and session_id to every message.

    Usage:
        log = StructuredLogger(__name__)
        log.info("Session started", extra={"event": "session.started"})
    """

    def __init__(self, name: str) -> None:
        self._logger = logging.getLogger(name)

    def _log(self, level: int, msg: str, **kwargs: Any) -> None:
        extra = kwargs.pop("extra", {})
        extra.setdefault("correlation_id", get_correlation_id())
        extra.setdefault("session_id", get_session_context())
        self._logger.log(level, msg, extra=extra, **kwargs)

    def info(self, msg: str, **kwargs: Any) -> None:
        self._log(logging.INFO, msg, **kwargs)

    def warning(self, msg: str, **kwargs: Any) -> None:
        self._log(logging.WARNING, msg, **kwargs)

    def error(self, msg: str, **kwargs: Any) -> None:
        self._log(logging.ERROR, msg, **kwargs)

    def debug(self, msg: str, **kwargs: Any) -> None:
        self._log(logging.DEBUG, msg, **kwargs)
