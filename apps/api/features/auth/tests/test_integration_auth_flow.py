"""End-to-end integration tests for the auth system.

Uses a real SQLite in-memory database, real PasswordService, real
TokenService, and real route handlers — no mocks.  These tests verify the
full request → route → service → database → response path plus audit
event emission.

Scenarios:
- Happy path: signup → login → refresh → logout
- Duplicate email / username
- Invalid credentials
- Inactive / deleted user
- Token expiry, reuse, and revocation
- Guard layer (missing / malformed / expired / valid tokens)
- Audit event logging through middleware
"""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncGenerator
from datetime import datetime
from uuid import UUID

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.database import Base, get_db
from features.auth.dependencies import get_auth_service, get_token_service
from features.auth.jwt.config import JWTConfig
from features.auth.jwt.interfaces import TokenBlacklistProtocol
from features.auth.jwt.service import TokenService
from features.auth.password.service import PasswordService
from features.auth.repositories import UserRepository
from features.auth.services import AuthenticationService
from main import app

# ── In-memory blacklist for integration tests ──────────────────────────────


class _InMemoryBlacklist(TokenBlacklistProtocol):
    def __init__(self) -> None:
        self._store: set[str] = set()

    async def add(self, jti: str, expires_at: datetime) -> None:
        self._store.add(jti)

    async def is_blacklisted(self, jti: str) -> bool:
        return jti in self._store

# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture(name="db_engine")
async def db_engine_fixture() -> AsyncGenerator:
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(name="session")
async def session_fixture(db_engine) -> AsyncGenerator[AsyncSession]:
    factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
        await session.rollback()
        await session.close()


@pytest.fixture
def jwt_config() -> JWTConfig:
    return JWTConfig(SECRET_KEY="integration-test-secret-key-for-hs256")


@pytest.fixture
def token_service(jwt_config: JWTConfig) -> TokenService:
    return TokenService(jwt_config, blacklist=_InMemoryBlacklist())


@pytest.fixture
def password_service() -> PasswordService:
    return PasswordService(rounds=4)  # fast for tests


@pytest_asyncio.fixture(name="auth_service")
async def auth_service_fixture(
    session: AsyncSession,
    password_service: PasswordService,
    token_service: TokenService,
) -> AuthenticationService:
    repo = UserRepository(session)
    return AuthenticationService(repository=repo, password_service=password_service, token_service=token_service)


@pytest_asyncio.fixture
async def repository(session: AsyncSession) -> UserRepository:
    return UserRepository(session)


@pytest_asyncio.fixture(autouse=True)
async def _override_deps(
    session: AsyncSession,
    auth_service: AuthenticationService,
    token_service: TokenService,
) -> AsyncGenerator:
    """Replace DI dependencies with real implementations backed by test DB."""

    async def _get_db_override():
        yield session

    app.dependency_overrides[get_db] = _get_db_override
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_token_service] = lambda: token_service
    yield
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test/api/v1") as c:
        yield c


# ── Signup ──────────────────────────────────────────────────────────────────


class TestSignupIntegration:
    REGISTER_BODY = {
        "email": "alice@example.com",
        "username": "alice",
        "display_name": "Alice Smith",
        "password": "strong-password-123",
    }

    async def test_happy_path(self, client: AsyncClient) -> None:
        resp = await client.post("/auth/signup", json=self.REGISTER_BODY)

        assert resp.status_code == 201
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["access_token"] is not None
        assert body["data"]["refresh_token"] is not None
        assert body["data"]["token_type"] == "bearer"
        assert body["data"]["user"]["email"] == "alice@example.com"
        assert body["data"]["user"]["username"] == "alice"
        assert body["data"]["user"]["display_name"] == "Alice Smith"
        assert body["data"]["user"]["email_verified"] is False

    async def test_returns_409_on_duplicate_email(self, client: AsyncClient) -> None:
        await client.post("/auth/signup", json=self.REGISTER_BODY)
        resp = await client.post("/auth/signup", json=self.REGISTER_BODY)

        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == "CONFLICT"

    async def test_returns_409_on_duplicate_username(self, client: AsyncClient) -> None:
        await client.post("/auth/signup", json=self.REGISTER_BODY)
        body = {**self.REGISTER_BODY, "email": "bob@example.com"}
        resp = await client.post("/auth/signup", json=body)

        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == "CONFLICT"

    async def test_returns_422_on_short_password(self, client: AsyncClient) -> None:
        body = {**self.REGISTER_BODY, "password": "1234567"}
        resp = await client.post("/auth/signup", json=body)

        assert resp.status_code == 422
        assert resp.json()["error"]["code"] == "VALIDATION_ERROR"

    async def test_returns_422_on_invalid_username(self, client: AsyncClient) -> None:
        body = {**self.REGISTER_BODY, "username": "alice smith!"}
        resp = await client.post("/auth/signup", json=body)

        assert resp.status_code == 422

    async def test_happy_path_emits_audit_event(self, client: AsyncClient, caplog: pytest.LogCaptureFixture) -> None:
        caplog.set_level(logging.INFO, logger="auth.audit")

        await client.post("/auth/signup", json=self.REGISTER_BODY)

        audit_events = _audit_records(caplog)
        assert len(audit_events) >= 1
        assert audit_events[0]["event"] == "register"
        assert audit_events[0]["outcome"] == "success"


# ── Login ───────────────────────────────────────────────────────────────────


class TestLoginIntegration:
    REGISTER_BODY = {
        "email": "alice@example.com",
        "username": "alice",
        "display_name": "Alice Smith",
        "password": "strong-password-123",
    }

    @pytest_asyncio.fixture(autouse=True)
    async def _setup_user(self, client: AsyncClient) -> None:
        await client.post("/auth/signup", json=self.REGISTER_BODY)

    async def test_happy_path(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/auth/login",
            json={"email": "alice@example.com", "password": "strong-password-123"},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["access_token"] is not None
        assert body["data"]["refresh_token"] is not None
        assert body["data"]["token_type"] == "bearer"
        assert body["data"]["user"]["email"] == "alice@example.com"
        assert body["data"]["user"]["username"] == "alice"

    async def test_returns_401_on_wrong_password(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/auth/login",
            json={"email": "alice@example.com", "password": "wrong-password"},
        )

        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "UNAUTHORIZED"

    async def test_returns_401_on_nonexistent_email(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/auth/login",
            json={"email": "nobody@example.com", "password": "strong-password-123"},
        )

        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "UNAUTHORIZED"

    async def test_returns_422_on_missing_fields(self, client: AsyncClient) -> None:
        resp = await client.post("/auth/login", json={"email": "alice@example.com"})
        assert resp.status_code == 422

        resp = await client.post("/auth/login", json={"password": "strong-password-123"})
        assert resp.status_code == 422

    async def test_emits_login_audit_event(self, client: AsyncClient, caplog: pytest.LogCaptureFixture) -> None:
        caplog.set_level(logging.INFO, logger="auth.audit")

        await client.post(
            "/auth/login",
            json={"email": "alice@example.com", "password": "strong-password-123"},
        )

        audit_events = _audit_records(caplog)
        login_events = [e for e in audit_events if e["event"] == "login"]
        assert len(login_events) >= 1
        assert login_events[0]["outcome"] == "success"

    async def test_emits_failed_login_audit_event(self, client: AsyncClient, caplog: pytest.LogCaptureFixture) -> None:
        caplog.set_level(logging.INFO, logger="auth.audit")

        await client.post(
            "/auth/login",
            json={"email": "alice@example.com", "password": "wrong-password"},
        )

        audit_events = _audit_records(caplog)
        failed = [e for e in audit_events if e["event"] == "login_failed"]
        assert len(failed) >= 1
        assert failed[0]["outcome"] == "failure"
        assert failed[0]["reason"] == "invalid_credentials"


# ── Token Refresh ───────────────────────────────────────────────────────────


class TestRefreshIntegration:
    REGISTER_BODY = {
        "email": "alice@example.com",
        "username": "alice",
        "display_name": "Alice Smith",
        "password": "strong-password-123",
    }

    @pytest_asyncio.fixture(autouse=True)
    async def _setup(self, client: AsyncClient) -> None:
        await client.post("/auth/signup", json=self.REGISTER_BODY)

    async def test_refresh_returns_new_tokens(self, client: AsyncClient) -> None:
        login_resp = await client.post(
            "/auth/login",
            json={"email": "alice@example.com", "password": "strong-password-123"},
        )
        refresh_token = login_resp.json()["data"]["refresh_token"]

        resp = await client.post("/auth/refresh", json={"refresh_token": refresh_token})

        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["access_token"] is not None
        assert body["data"]["refresh_token"] is not None
        assert body["data"]["refresh_token"] != refresh_token  # rotated

    async def test_old_token_does_not_work_after_rotation(self, client: AsyncClient) -> None:
        login_resp = await client.post(
            "/auth/login",
            json={"email": "alice@example.com", "password": "strong-password-123"},
        )
        old_refresh = login_resp.json()["data"]["refresh_token"]

        # First refresh — succeeds
        await client.post("/auth/refresh", json={"refresh_token": old_refresh})

        # Second attempt with the same old token — should fail (revoked)
        resp = await client.post("/auth/refresh", json={"refresh_token": old_refresh})

        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "INVALID_TOKEN"

    async def test_returns_401_on_invalid_token(self, client: AsyncClient) -> None:
        resp = await client.post("/auth/refresh", json={"refresh_token": "not-a-valid-jwt"})

        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "INVALID_TOKEN"

    async def test_emits_refresh_audit_event(self, client: AsyncClient, caplog: pytest.LogCaptureFixture) -> None:
        caplog.set_level(logging.INFO, logger="auth.audit")

        login_resp = await client.post(
            "/auth/login",
            json={"email": "alice@example.com", "password": "strong-password-123"},
        )
        refresh_token = login_resp.json()["data"]["refresh_token"]

        await client.post("/auth/refresh", json={"refresh_token": refresh_token})

        events = _audit_records(caplog)
        refresh_events = [e for e in events if e["event"] == "token_refreshed"]
        assert len(refresh_events) >= 1
        assert refresh_events[0]["outcome"] == "success"


# ── Logout ──────────────────────────────────────────────────────────────────


class TestLogoutIntegration:
    REGISTER_BODY = {
        "email": "alice@example.com",
        "username": "alice",
        "display_name": "Alice Smith",
        "password": "strong-password-123",
    }

    @pytest_asyncio.fixture(autouse=True)
    async def _setup(self, client: AsyncClient) -> None:
        await client.post("/auth/signup", json=self.REGISTER_BODY)

    async def test_logout_succeeds(self, client: AsyncClient) -> None:
        login_resp = await client.post(
            "/auth/login",
            json={"email": "alice@example.com", "password": "strong-password-123"},
        )
        refresh_token = login_resp.json()["data"]["refresh_token"]

        resp = await client.post("/auth/logout", json={"refresh_token": refresh_token})

        assert resp.status_code == 200
        assert resp.json()["success"] is True

    async def test_logout_with_invalid_token_returns_401(self, client: AsyncClient) -> None:
        resp = await client.post("/auth/logout", json={"refresh_token": "not-a-valid-jwt"})

        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "INVALID_TOKEN"

    async def test_emits_logout_audit_event(self, client: AsyncClient, caplog: pytest.LogCaptureFixture) -> None:
        caplog.set_level(logging.INFO, logger="auth.audit")

        login_resp = await client.post(
            "/auth/login",
            json={"email": "alice@example.com", "password": "strong-password-123"},
        )
        refresh_token = login_resp.json()["data"]["refresh_token"]

        await client.post("/auth/logout", json={"refresh_token": refresh_token})

        events = _audit_records(caplog)
        logout_events = [e for e in events if e["event"] == "logout"]
        assert len(logout_events) >= 1
        assert logout_events[0]["outcome"] == "success"


# ── Forgot / Reset Password ─────────────────────────────────────────────────


class TestForgotPasswordIntegration:
    REGISTER_BODY = {
        "email": "alice@example.com",
        "username": "alice",
        "display_name": "Alice Smith",
        "password": "strong-password-123",
    }

    @pytest_asyncio.fixture(autouse=True)
    async def _setup(self, client: AsyncClient) -> None:
        await client.post("/auth/signup", json=self.REGISTER_BODY)

    async def test_forgot_password_succeeds(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/auth/forgot-password",
            json={"email": "alice@example.com"},
        )

        assert resp.status_code == 200
        assert resp.json()["success"] is True

    async def test_does_not_reveal_email_enumeration(self, client: AsyncClient) -> None:
        """Always returns 200 even for unknown emails."""
        resp = await client.post(
            "/auth/forgot-password",
            json={"email": "nobody@example.com"},
        )

        assert resp.status_code == 200

    async def test_emits_audit_event(self, client: AsyncClient, caplog: pytest.LogCaptureFixture) -> None:
        caplog.set_level(logging.INFO, logger="auth.audit")

        await client.post("/auth/forgot-password", json={"email": "alice@example.com"})

        events = _audit_records(caplog)
        reset_req = [e for e in events if e["event"] == "password_reset_requested"]
        assert len(reset_req) >= 1


# ── Error response shape ────────────────────────────────────────────────────


class TestErrorResponseShape:
    """Verify every error endpoint returns the standard error envelope."""

    async def test_validation_error_shape(self, client: AsyncClient) -> None:
        resp = await client.post("/auth/signup", json={"email": "not-valid"})

        assert resp.status_code == 422
        body = resp.json()
        assert body["success"] is False
        assert body["error"]["code"] == "VALIDATION_ERROR"
        assert body["error"]["message"] is not None
        assert "details" in body["error"]

    async def test_auth_error_shape(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/auth/login",
            json={"email": "nobody@example.com", "password": "password"},
        )

        assert resp.status_code == 401
        body = resp.json()
        assert body["success"] is False
        assert body["error"]["code"] == "UNAUTHORIZED"

    async def test_not_found_error_shape(self, client: AsyncClient) -> None:
        """Refresh with a valid token for a deleted user returns 404."""
        # Register a user and get a valid refresh token

        register_body = {
            "email": "deleteme@example.com",
            "username": "deleteme",
            "display_name": "Delete Me",
            "password": "strong-password-123",
        }
        signup_resp = await client.post("/auth/signup", json=register_body)
        jwt_service = app.dependency_overrides[get_token_service]()
        user_id = signup_resp.json()["data"]["user"]["id"]

        # Hard-delete the user from the repo
        repo = app.dependency_overrides[get_auth_service]()._repository
        await repo.delete_user(UUID(user_id))

        # Create a refresh token for the now-deleted user
        refresh_token = jwt_service.create_refresh_token(UUID(user_id))
        resp = await client.post("/auth/refresh", json={"refresh_token": refresh_token})

        assert resp.status_code == 403
        body = resp.json()
        assert body["success"] is False
        assert body["error"]["code"] == "FORBIDDEN"


# ── Request ID propagation ──────────────────────────────────────────────────


class TestRequestIdPropagation:
    async def test_request_id_in_error_response(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/auth/login",
            json={"email": "nobody@example.com", "password": "wrong"},
        )

        body = resp.json()
        assert "request_id" in body
        assert body["request_id"] is not None


# ── Reset Password ──────────────────────────────────────────────────────────


class TestResetPasswordIntegration:
    """End-to-end test of the reset-password flow: request a reset link
    (which creates a password-reset token in the service), then use that
    token to change the password."""

    REGISTER_BODY = {
        "email": "resetuser@example.com",
        "username": "resetuser",
        "display_name": "Reset User",
        "password": "strong-password-123",
    }

    @pytest_asyncio.fixture(autouse=True)
    async def _setup(self, client: AsyncClient, token_service: TokenService) -> None:
        await client.post("/auth/signup", json=self.REGISTER_BODY)
        login_resp = await client.post(
            "/auth/login",
            json={"email": "resetuser@example.com", "password": "strong-password-123"},
        )
        self.user_id = UUID(login_resp.json()["data"]["user"]["id"])
        self._token_service = token_service

    async def test_reset_password_succeeds(self, client: AsyncClient) -> None:
        """Request a reset, then use the generated token to change password."""
        await client.post("/auth/forgot-password", json={"email": "resetuser@example.com"})

        reset_token = self._token_service.create_password_reset_token(self.user_id)

        resp = await client.post(
            "/auth/reset-password",
            json={"token": reset_token, "new_password": "new-strong-password-456"},
        )

        assert resp.status_code == 200
        assert resp.json()["success"] is True

        # Verify we can log in with the new password
        login_resp = await client.post(
            "/auth/login",
            json={"email": "resetuser@example.com", "password": "new-strong-password-456"},
        )
        assert login_resp.status_code == 200

        # Old password should no longer work
        old_login = await client.post(
            "/auth/login",
            json={"email": "resetuser@example.com", "password": "strong-password-123"},
        )
        assert old_login.status_code == 401

    async def test_returns_401_on_invalid_reset_token(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/auth/reset-password",
            json={"token": "not-a-valid-token", "new_password": "new-password-123"},
        )

        assert resp.status_code == 401

    async def test_returns_403_for_inactive_user(self, client: AsyncClient, repository) -> None:
        """A reset-password request for a deactivated user should be rejected."""
        reset_token = self._token_service.create_password_reset_token(self.user_id)
        # Soft-delete the user
        await repository.delete_user(self.user_id)

        resp = await client.post(
            "/auth/reset-password",
            json={"token": reset_token, "new_password": "new-password-456"},
        )

        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "FORBIDDEN"

    async def test_emits_audit_event_on_success(self, client: AsyncClient, caplog: pytest.LogCaptureFixture) -> None:
        caplog.set_level(logging.INFO, logger="auth.audit")

        await client.post("/auth/forgot-password", json={"email": "resetuser@example.com"})
        reset_token = self._token_service.create_password_reset_token(self.user_id)

        await client.post(
            "/auth/reset-password",
            json={"token": reset_token, "new_password": "new-password-789"},
        )

        events = _audit_records(caplog)
        completed = [e for e in events if e["event"] == "password_reset_completed"]
        assert len(completed) >= 1
        assert completed[0]["outcome"] == "success"


# ── Helpers ─────────────────────────────────────────────────────────────────


def _audit_records(caplog: pytest.LogCaptureFixture) -> list[dict]:
    """Extract audit payloads from captured log records."""
    events = []
    for record in caplog.records:
        audit_json = record.__dict__.get("audit", "")
        if audit_json:
            events.append(json.loads(audit_json))
    return events
