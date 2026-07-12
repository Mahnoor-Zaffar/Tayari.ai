from __future__ import annotations

import hashlib
import json
import logging
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from fastapi import Request, Response

from core.logging import request_id

log = logging.getLogger("auth.audit")


# ── Event types ─────────────────────────────────────────────────────────────


class AuthEvent(StrEnum):
    REGISTER = "register"
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    PASSWORD_RESET_REQUESTED = "password_reset_requested"
    PASSWORD_RESET_COMPLETED = "password_reset_completed"
    TOKEN_REFRESHED = "token_refreshed"
    TOKEN_REFRESH_REJECTED = "token_refresh_rejected"


# ── Helpers ─────────────────────────────────────────────────────────────────


def _hash_email(email: str) -> str:
    """SHA-256 prefix — never the full address."""
    return hashlib.sha256(email.lower().encode()).hexdigest()[:16]


def _fmt(ts: datetime) -> str:
    return ts.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


# ── Structured audit record ─────────────────────────────────────────────────


class AuditEvent:
    """Lightweight container for audit data.

    Sensitive fields (passwords, raw tokens, full emails) are **never**
    stored here.
    """

    __slots__ = (
        "event",
        "user_id",
        "email_hash",
        "ip_address",
        "user_agent",
        "request_id",
        "outcome",
        "failure_reason",
        "metadata",
    )

    def __init__(
        self,
        event: AuthEvent,
        *,
        user_id: str | None = None,
        email: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        outcome: str = "success",
        failure_reason: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.event = event
        self.user_id = user_id
        self.email_hash = _hash_email(email) if email else None
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.request_id = request_id.get() or ""
        self.outcome = outcome
        self.failure_reason = failure_reason
        self.metadata = metadata or {}

    def asdict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "ts": _fmt(datetime.now(UTC)),
            "event": self.event.value,
            "user_id": self.user_id,
            "email_hash": self.email_hash,
            "ip": self.ip_address,
            "user_agent": self.user_agent,
            "request_id": self.request_id,
            "outcome": self.outcome,
        }
        if self.failure_reason:
            d["reason"] = self.failure_reason
        if self.metadata:
            d.update(self.metadata)
        return d


# ── Audit logger ────────────────────────────────────────────────────────────


class AuditLogger:
    """Per-request audit logger pre-configured with transport-layer context.

    Emits structured JSON to the ``auth.audit`` logger.  Attach to
    ``request.state.audit`` via the middleware so route handlers can
    log events without boilerplate::

        request.state.audit.log(AuditEvent(AuthEvent.LOGIN, user_id=..., email=...))
    """

    def __init__(self, ip_address: str | None = None, user_agent: str | None = None) -> None:
        self._ip = ip_address
        self._ua = user_agent

    def log(self, event: AuditEvent) -> None:
        if event.ip_address is None:
            event.ip_address = self._ip
        if event.user_agent is None:
            event.user_agent = self._ua
        log.info("auth_event", extra={"audit": json.dumps(event.asdict(), default=str)})


# ── FastAPI middleware ──────────────────────────────────────────────────────


async def auth_audit_middleware(request: Request, call_next) -> Response:
    """Extract IP / User-Agent once, attach an ``AuditLogger`` to
    ``request.state.audit``.

    Sensitive data is **never** captured here — only what the transport
    layer provides (headers, client host).
    """
    ip_address: str | None = request.client.host if request.client else None
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        ip_address = forwarded.split(",")[0].strip()

    user_agent = request.headers.get("User-Agent")

    request.state.audit = AuditLogger(ip_address=ip_address, user_agent=user_agent)

    return await call_next(request)
