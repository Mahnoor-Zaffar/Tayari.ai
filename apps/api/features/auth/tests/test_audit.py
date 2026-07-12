"""Unit tests for the structured auth audit system.

Covers:
- AuthEvent enum values
- AuditEvent construction, email hashing, and asdict() output
- AuditLogger structured JSON output
- No sensitive data (passwords, tokens, full emails) in log records
"""

from __future__ import annotations

import json
import logging
from uuid import uuid4

import pytest
from fastapi import FastAPI, Request
from httpx import ASGITransport, AsyncClient

from core.audit import AuditEvent, AuditLogger, AuthEvent, auth_audit_middleware
from core.logging import request_id


def _build_test_app() -> FastAPI:
    app = FastAPI()

    app.middleware("http")(auth_audit_middleware)

    @app.get("/check-audit")
    async def check_audit(request: Request):
        return {"has_audit": hasattr(request.state, "audit")}

    @app.get("/audit-ip")
    async def audit_ip(request: Request):
        return {"ip": request.state.audit._ip}

    @app.get("/audit-ua")
    async def audit_ua(request: Request):
        return {"ua": request.state.audit._ua}

    @app.get("/emit-login-event")
    async def emit_event(request: Request):
        request.state.audit.log(
            AuditEvent(
                AuthEvent.LOGIN,
                user_id=str(uuid4()),
                email="alice@example.com",
            )
        )
        return {"ok": True}

    return app


# ── AuthEvent enum ──────────────────────────────────────────────────────────


class TestAuthEvent:
    def test_all_events_have_string_values(self) -> None:
        for event in AuthEvent:
            assert isinstance(event.value, str)
            assert len(event.value) > 0

    def test_unique_values(self) -> None:
        values = [e.value for e in AuthEvent]
        assert len(values) == len(set(values))

    def test_register(self) -> None:
        assert AuthEvent.REGISTER == "register"

    def test_login(self) -> None:
        assert AuthEvent.LOGIN == "login"

    def test_logout(self) -> None:
        assert AuthEvent.LOGOUT == "logout"

    def test_login_failed(self) -> None:
        assert AuthEvent.LOGIN_FAILED == "login_failed"

    def test_password_reset_requested(self) -> None:
        assert AuthEvent.PASSWORD_RESET_REQUESTED == "password_reset_requested"

    def test_password_reset_completed(self) -> None:
        assert AuthEvent.PASSWORD_RESET_COMPLETED == "password_reset_completed"

    def test_token_refreshed(self) -> None:
        assert AuthEvent.TOKEN_REFRESHED == "token_refreshed"

    def test_token_refresh_rejected(self) -> None:
        assert AuthEvent.TOKEN_REFRESH_REJECTED == "token_refresh_rejected"


# ── AuditEvent construction ─────────────────────────────────────────────────


class TestAuditEventConstruction:
    def test_minimal_construction(self) -> None:
        event = AuditEvent(AuthEvent.LOGOUT)
        assert event.event == AuthEvent.LOGOUT
        assert event.user_id is None
        assert event.email_hash is None
        assert event.outcome == "success"
        assert event.failure_reason is None

    def test_with_all_fields(self) -> None:
        user_id = str(uuid4())
        event = AuditEvent(
            AuthEvent.LOGIN,
            user_id=user_id,
            email="alice@example.com",
            ip_address="192.168.1.1",
            user_agent="test-agent",
            outcome="failure",
            failure_reason="invalid_credentials",
            metadata={"attempts": 3},
        )
        assert event.user_id == user_id
        assert event.email_hash is not None
        assert len(event.email_hash) == 16  # SHA-256 prefix
        assert event.ip_address == "192.168.1.1"
        assert event.user_agent == "test-agent"
        assert event.outcome == "failure"
        assert event.failure_reason == "invalid_credentials"
        assert event.metadata == {"attempts": 3}


# ── Email hashing ───────────────────────────────────────────────────────────


class TestEmailHash:
    def test_never_contains_full_email(self) -> None:
        event = AuditEvent(AuthEvent.REGISTER, email="sensitive@example.com")
        assert event.email_hash is not None
        assert "@" not in event.email_hash
        assert "sensitive" not in event.email_hash
        assert "example" not in event.email_hash

    def test_is_deterministic_for_same_email(self) -> None:
        e1 = AuditEvent(AuthEvent.LOGIN, email="alice@example.com")
        e2 = AuditEvent(AuthEvent.LOGIN, email="alice@example.com")
        assert e1.email_hash == e2.email_hash

    def test_differs_for_different_emails(self) -> None:
        e1 = AuditEvent(AuthEvent.LOGIN, email="alice@example.com")
        e2 = AuditEvent(AuthEvent.LOGIN, email="bob@example.com")
        assert e1.email_hash != e2.email_hash

    def test_case_insensitive(self) -> None:
        e1 = AuditEvent(AuthEvent.LOGIN, email="Alice@Example.Com")
        e2 = AuditEvent(AuthEvent.LOGIN, email="alice@example.com")
        assert e1.email_hash == e2.email_hash

    def test_none_when_email_not_provided(self) -> None:
        event = AuditEvent(AuthEvent.LOGOUT)
        assert event.email_hash is None


# ── asdict() output ─────────────────────────────────────────────────────────


class TestAsDict:
    def test_contains_all_expected_keys_for_success(self) -> None:
        event = AuditEvent(AuthEvent.LOGIN, user_id=str(uuid4()), email="a@b.com")
        d = event.asdict()

        assert "ts" in d
        assert d["event"] == "login"
        assert d["user_id"] is not None
        assert d["email_hash"] is not None
        assert d["outcome"] == "success"
        assert "reason" not in d
        assert "ip" in d
        assert "user_agent" in d
        assert "request_id" in d

    def test_includes_reason_on_failure(self) -> None:
        event = AuditEvent(AuthEvent.LOGIN_FAILED, outcome="failure", failure_reason="invalid_credentials")
        d = event.asdict()

        assert d["reason"] == "invalid_credentials"
        assert d["outcome"] == "failure"

    def test_includes_metadata(self) -> None:
        event = AuditEvent(
            AuthEvent.TOKEN_REFRESH_REJECTED,
            outcome="failure",
            failure_reason="replay_detected",
            metadata={"token_family": "fam-123"},
        )
        d = event.asdict()

        assert d["token_family"] == "fam-123"

    def test_never_contains_password_or_token(self) -> None:
        event = AuditEvent(AuthEvent.REGISTER, email="user@example.com")
        d = json.dumps(event.asdict()).lower()

        assert "password" not in d
        assert "secret" not in d
        assert "token_value" not in d
        assert event.asdict().get("password") is None
        assert event.asdict().get("token") is None

    def test_timestamp_format(self) -> None:
        event = AuditEvent(AuthEvent.LOGIN)
        ts = event.asdict()["ts"]
        # ISO 8601 with Z suffix
        assert ts.endswith("Z")
        assert "T" in ts

    def test_ip_is_optional(self) -> None:
        event = AuditEvent(AuthEvent.LOGIN)
        assert event.asdict()["ip"] is None

    def test_user_id_is_optional(self) -> None:
        event = AuditEvent(AuthEvent.LOGOUT)
        assert event.asdict()["user_id"] is None


# ── AuditLogger ─────────────────────────────────────────────────────────────


class TestAuditLogger:
    def test_emits_structured_json_record(self, caplog: pytest.LogCaptureFixture) -> None:
        caplog.set_level(logging.INFO, logger="auth.audit")

        logger = AuditLogger(ip_address="10.0.0.1", user_agent="test-agent")
        event = AuditEvent(AuthEvent.LOGIN, user_id=str(uuid4()), email="alice@example.com")

        logger.log(event)

        assert len(caplog.records) == 1
        record = caplog.records[0]
        assert record.name == "auth.audit"
        assert record.levelname == "INFO"

        # Extract the audit payload from the extra dict
        audit_json = record.__dict__.get("audit", "")
        assert audit_json, "audit extra field not found in log record"
        payload = json.loads(audit_json)

        assert payload["event"] == "login"
        assert payload["user_id"] == event.user_id
        assert payload["email_hash"] == event.email_hash
        assert payload["ip"] == "10.0.0.1"
        assert "password" not in json.dumps(payload).lower()

    def test_backfills_ip_and_ua_from_constructor(self) -> None:
        logger = AuditLogger(ip_address="192.168.1.1", user_agent="curl/8.0")

        event = AuditEvent(AuthEvent.REGISTER, email="test@example.com")
        logger.log(event)

        assert event.ip_address == "192.168.1.1"
        assert event.user_agent == "curl/8.0"

    def test_passes_existing_ip_without_overwrite(self) -> None:
        logger = AuditLogger(ip_address="10.0.0.1", user_agent="agent")

        event = AuditEvent(AuthEvent.LOGIN, email="test@example.com", ip_address="192.168.1.1")
        logger.log(event)

        assert event.ip_address == "192.168.1.1"

    def test_request_id_in_log_record(self, caplog: pytest.LogCaptureFixture) -> None:
        """Verify the audit record carries the current request_id."""
        caplog.set_level(logging.INFO, logger="auth.audit")
        rid = str(uuid4())
        request_id.set(rid)

        logger = AuditLogger()
        event = AuditEvent(AuthEvent.LOGOUT)
        logger.log(event)

        audit_json = caplog.records[0].__dict__.get("audit", "")
        payload = json.loads(audit_json)
        assert payload["request_id"] == rid


# ── AuditMiddleware ─────────────────────────────────────────────────────────


class FakeApp:
    """Minimal ASGI app used to test the middleware in isolation."""

    async def __call__(self, scope, receive, send) -> None:
        pass


class TestAuditMiddleware:
    async def test_attaches_audit_logger_to_request_state(self) -> None:
        """Verify the middleware adds `request.state.audit`."""
        transport = ASGITransport(app=_build_test_app())
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/check-audit")

        assert resp.status_code == 200
        assert resp.json()["has_audit"] is True

    async def test_extracts_ip_from_client_host(self) -> None:
        transport = ASGITransport(app=_build_test_app())
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/audit-ip")

        assert resp.status_code == 200
        # httpx test client sets client host to 127.0.0.1
        assert resp.json()["ip"] == "127.0.0.1"

    async def test_extracts_user_agent(self) -> None:
        transport = ASGITransport(app=_build_test_app())
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/audit-ua", headers={"User-Agent": "test-bot/1.0"})

        assert resp.status_code == 200
        assert resp.json()["ua"] == "test-bot/1.0"

    async def test_handles_x_forwarded_for(self) -> None:
        """When X-Forwarded-For is present, use its first value over client.host."""
        transport = ASGITransport(app=_build_test_app())
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(
                "/audit-ip",
                headers={"X-Forwarded-For": "203.0.113.5, 10.0.0.1"},
            )

        assert resp.status_code == 200
        assert resp.json()["ip"] == "203.0.113.5"

    async def test_audit_event_flow_through_middleware(self, caplog: pytest.LogCaptureFixture) -> None:
        """Full flow: middleware attaches AuditLogger → route emits event →
        log record contains IP and UA that the middleware captured."""
        caplog.set_level(logging.INFO, logger="auth.audit")

        transport = ASGITransport(app=_build_test_app())
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await client.get(
                "/emit-login-event",
                headers={
                    "User-Agent": "test-agent/1.0",
                    "X-Forwarded-For": "10.0.0.5",
                },
            )

        assert len(caplog.records) >= 1
        audit_json = caplog.records[0].__dict__.get("audit", "")
        payload = json.loads(audit_json)
        assert payload["event"] == "login"
        assert payload["ip"] == "10.0.0.5"
        assert payload["user_agent"] == "test-agent/1.0"
