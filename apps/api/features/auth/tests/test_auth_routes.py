from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from features.auth.dependencies import get_auth_service
from features.auth.domain.user import User
from features.auth.exceptions import (
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    InvalidTokenError,
    UsernameAlreadyExistsError,
    UserNotActiveError,
    UserNotFoundError,
)
from features.auth.services import AuthResult, RegistrationData
from main import app


@pytest.fixture
def mock_auth_service() -> MagicMock:
    svc = MagicMock()
    svc.register = AsyncMock()
    svc.login = AsyncMock()
    svc.refresh = AsyncMock()
    return svc


@pytest.fixture
def mock_token_service() -> MagicMock:
    svc = MagicMock()
    svc.peek = MagicMock(return_value={})
    svc.revoke_family = AsyncMock()
    return svc


@pytest.fixture
def client(mock_auth_service: MagicMock, mock_token_service: MagicMock) -> AsyncClient:
    from features.auth.dependencies import get_token_service

    app.dependency_overrides[get_auth_service] = lambda: mock_auth_service
    app.dependency_overrides[get_token_service] = lambda: mock_token_service
    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://test/api/v1")
    yield client
    app.dependency_overrides.clear()


VALID_BODY = {
    "email": "alice@example.com",
    "username": "alice",
    "display_name": "Alice Smith",
    "password": "strong-password-123",
}


def _make_user() -> User:
    return User(
        id=uuid4(),
        email="alice@example.com",
        username="alice",
        display_name="Alice Smith",
        password_hash="$2b$12$hashed",
        email_verified=False,
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


class TestRegister:
    async def test_returns_201_on_success(self, client: AsyncClient, mock_auth_service: MagicMock) -> None:
        user = _make_user()
        mock_auth_service.register.return_value = AuthResult(
            user=user,
            access_token="access-token",
            refresh_token="refresh-token",
        )

        resp = await client.post("/auth/signup", json=VALID_BODY)

        assert resp.status_code == 201
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["access_token"] == "access-token"
        assert body["data"]["refresh_token"] == "refresh-token"
        assert body["data"]["token_type"] == "bearer"
        assert body["data"]["user"]["id"] == str(user.id)
        assert body["data"]["user"]["email"] == "alice@example.com"
        assert body["data"]["user"]["username"] == "alice"

        mock_auth_service.register.assert_awaited_once()
        call_data: RegistrationData = mock_auth_service.register.call_args[0][0]
        assert call_data.email == "alice@example.com"
        assert call_data.username == "alice"
        assert call_data.password == "strong-password-123"

    async def test_returns_409_on_duplicate_email(self, client: AsyncClient, mock_auth_service: MagicMock) -> None:
        mock_auth_service.register.side_effect = EmailAlreadyExistsError("Email already registered")

        resp = await client.post("/auth/signup", json=VALID_BODY)

        assert resp.status_code == 409
        body = resp.json()
        assert body["success"] is False
        assert body["error"]["code"] == "CONFLICT"

    async def test_returns_409_on_duplicate_username(self, client: AsyncClient, mock_auth_service: MagicMock) -> None:
        mock_auth_service.register.side_effect = UsernameAlreadyExistsError("Username already taken")

        resp = await client.post("/auth/signup", json=VALID_BODY)

        assert resp.status_code == 409
        body = resp.json()
        assert body["success"] is False
        assert body["error"]["code"] == "CONFLICT"

    async def test_returns_422_on_missing_email(self, client: AsyncClient, mock_auth_service: MagicMock) -> None:
        resp = await client.post(
            "/auth/signup", json={"username": "alice", "display_name": "A", "password": "12345678"}
        )

        assert resp.status_code == 422
        body = resp.json()
        assert body["success"] is False
        assert body["error"]["code"] == "VALIDATION_ERROR"

    async def test_returns_422_on_invalid_email(self, client: AsyncClient, mock_auth_service: MagicMock) -> None:
        body = {**VALID_BODY, "email": "not-an-email"}
        resp = await client.post("/auth/signup", json=body)

        assert resp.status_code == 422

    async def test_returns_422_on_short_username(self, client: AsyncClient, mock_auth_service: MagicMock) -> None:
        body = {**VALID_BODY, "username": "ab"}
        resp = await client.post("/auth/signup", json=body)

        assert resp.status_code == 422

    async def test_returns_422_on_short_password(self, client: AsyncClient, mock_auth_service: MagicMock) -> None:
        body = {**VALID_BODY, "password": "short"}
        resp = await client.post("/auth/signup", json=body)

        assert resp.status_code == 422

    async def test_returns_422_on_invalid_username_chars(
        self, client: AsyncClient, mock_auth_service: MagicMock
    ) -> None:
        body = {**VALID_BODY, "username": "alice smith!"}
        resp = await client.post("/auth/signup", json=body)

        assert resp.status_code == 422


LOGIN_BODY = {"email": "alice@example.com", "password": "correct-password"}


class TestLogin:
    async def test_returns_200_on_valid_credentials(self, client: AsyncClient, mock_auth_service: MagicMock) -> None:
        user = _make_user()
        mock_auth_service.login.return_value = AuthResult(
            user=user,
            access_token="access-token",
            refresh_token="refresh-token",
        )

        resp = await client.post("/auth/login", json=LOGIN_BODY)

        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["access_token"] == "access-token"
        assert body["data"]["refresh_token"] == "refresh-token"
        assert body["data"]["token_type"] == "bearer"
        assert body["data"]["user"]["id"] == str(user.id)
        assert body["data"]["user"]["email"] == "alice@example.com"

        mock_auth_service.login.assert_awaited_once_with("alice@example.com", "correct-password")

    async def test_returns_401_on_invalid_credentials(self, client: AsyncClient, mock_auth_service: MagicMock) -> None:
        mock_auth_service.login.side_effect = InvalidCredentialsError("Invalid email or password")

        resp = await client.post("/auth/login", json=LOGIN_BODY)

        assert resp.status_code == 401
        body = resp.json()
        assert body["success"] is False
        assert body["error"]["code"] == "UNAUTHORIZED"

    async def test_returns_403_on_inactive_account(self, client: AsyncClient, mock_auth_service: MagicMock) -> None:
        mock_auth_service.login.side_effect = UserNotActiveError("Account is disabled")

        resp = await client.post("/auth/login", json=LOGIN_BODY)

        assert resp.status_code == 403
        body = resp.json()
        assert body["success"] is False
        assert body["error"]["code"] == "FORBIDDEN"

    async def test_returns_422_on_missing_email(self, client: AsyncClient, mock_auth_service: MagicMock) -> None:
        resp = await client.post("/auth/login", json={"password": "password"})

        assert resp.status_code == 422

    async def test_returns_422_on_invalid_email_format(self, client: AsyncClient, mock_auth_service: MagicMock) -> None:
        resp = await client.post("/auth/login", json={"email": "not-email", "password": "password"})

        assert resp.status_code == 422

    async def test_returns_422_on_missing_password(self, client: AsyncClient, mock_auth_service: MagicMock) -> None:
        resp = await client.post("/auth/login", json={"email": "a@b.com"})

        assert resp.status_code == 422


REFRESH_BODY = {"refresh_token": "valid-refresh-token"}


class TestRefresh:
    async def test_returns_200_on_valid_token(self, client: AsyncClient, mock_auth_service: MagicMock) -> None:
        user = _make_user()
        mock_auth_service.refresh.return_value = AuthResult(
            user=user,
            access_token="new-access-token",
            refresh_token="new-refresh-token",
        )

        resp = await client.post("/auth/refresh", json=REFRESH_BODY)

        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["access_token"] == "new-access-token"
        assert body["data"]["refresh_token"] == "new-refresh-token"
        assert body["data"]["token_type"] == "bearer"
        assert body["data"]["user"]["id"] == str(user.id)
        assert body["data"]["user"]["email"] == "alice@example.com"

        mock_auth_service.refresh.assert_awaited_once_with("valid-refresh-token")

    async def test_returns_401_on_invalid_token(self, client: AsyncClient, mock_auth_service: MagicMock) -> None:
        mock_auth_service.refresh.side_effect = InvalidTokenError("bad token")

        resp = await client.post("/auth/refresh", json=REFRESH_BODY)

        assert resp.status_code == 401
        body = resp.json()
        assert body["success"] is False
        assert body["error"]["code"] == "INVALID_TOKEN"

    async def test_returns_401_on_reused_token(
        self, client: AsyncClient, mock_auth_service: MagicMock, mock_token_service: MagicMock
    ) -> None:
        mock_token_service.peek.return_value = {
            "token_family": "family-1",
            "exp": 9999999999,
            "sub": "user-1",
        }
        mock_auth_service.refresh.side_effect = InvalidTokenError("Token has been revoked")

        resp = await client.post("/auth/refresh", json=REFRESH_BODY)

        assert resp.status_code == 401
        mock_token_service.peek.assert_called_once_with("valid-refresh-token")
        mock_token_service.revoke_family.assert_awaited_once()

    async def test_returns_404_on_user_not_found(self, client: AsyncClient, mock_auth_service: MagicMock) -> None:
        mock_auth_service.refresh.side_effect = UserNotFoundError("User not found")

        resp = await client.post("/auth/refresh", json=REFRESH_BODY)

        assert resp.status_code == 404
        body = resp.json()
        assert body["success"] is False
        assert body["error"]["code"] == "NOT_FOUND"

    async def test_returns_403_on_inactive_user(self, client: AsyncClient, mock_auth_service: MagicMock) -> None:
        mock_auth_service.refresh.side_effect = UserNotActiveError("Account disabled")

        resp = await client.post("/auth/refresh", json=REFRESH_BODY)

        assert resp.status_code == 403
        body = resp.json()
        assert body["success"] is False
        assert body["error"]["code"] == "FORBIDDEN"

    async def test_returns_422_on_empty_body(self, client: AsyncClient, mock_auth_service: MagicMock) -> None:
        resp = await client.post("/auth/refresh", json={})

        assert resp.status_code == 422
        body = resp.json()
        assert body["success"] is False
        assert body["error"]["code"] == "VALIDATION_ERROR"
