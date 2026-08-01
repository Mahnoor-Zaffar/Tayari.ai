from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import Depends
from httpx import ASGITransport, AsyncClient

from features.auth.dependencies import get_token_service
from features.auth.domain.user import User
from features.auth.guard import (
    PermissionChecker,
    RoleChecker,
    get_current_user,
    get_optional_user,
    get_user_repo,
)
from features.auth.jwt.models import TokenPayload
from features.auth.repositories import UserRepository
from main import app


def _make_user() -> User:
    return User(
        id=uuid4(),
        email="alice@example.com",
        username="alice",
        display_name="Alice Smith",
        password_hash="$2b$12$hashed",
        email_verified=True,
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def _make_payload(
    *,
    sub: str | None = None,
    roles: list[str] | None = None,
    permissions: list[str] | None = None,
) -> TokenPayload:
    return TokenPayload(
        sub=sub or str(uuid4()),
        type="access",
        exp=datetime.now(UTC),
        iat=datetime.now(UTC),
        jti=str(uuid4()),
        iss="tayari-ai",
        aud="tayari-api",
        roles=roles or ["user"],
        permissions=permissions or [],
    )


@pytest.fixture(autouse=True)
def _clear_overrides():
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def mock_token_service() -> MagicMock:
    svc = MagicMock()
    svc.verify = AsyncMock()
    return svc


@pytest.fixture
def mock_user_repo() -> MagicMock:
    repo = MagicMock(spec=UserRepository)
    repo.find_by_id = AsyncMock()
    return repo


@pytest.fixture
def override_deps(
    mock_token_service: MagicMock,
    mock_user_repo: MagicMock,
) -> None:
    app.dependency_overrides[get_token_service] = lambda: mock_token_service
    app.dependency_overrides[get_user_repo] = lambda: mock_user_repo


class TestGetCurrentUser:
    async def test_returns_user_on_valid_token(
        self,
        override_deps: None,
        mock_token_service: MagicMock,
        mock_user_repo: MagicMock,
    ) -> None:
        user = _make_user()
        payload = _make_payload(sub=str(user.id), roles=["admin"], permissions=["users:write"])
        mock_token_service.verify.return_value = payload
        mock_user_repo.find_by_id.return_value = user

        @app.get("/test/me")
        async def _test_me(authed_user=Depends(get_current_user)):
            return {
                "id": str(authed_user.id),
                "email": authed_user.email,
                "roles": authed_user.roles,
                "permissions": authed_user.permissions,
            }

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/test/me", headers={"Authorization": "Bearer valid-token"})

        assert resp.status_code == 200
        body = resp.json()
        assert body["email"] == "alice@example.com"
        assert body["roles"] == ["admin"]
        assert body["permissions"] == ["users:write"]

    async def test_raises_401_on_missing_header(
        self,
        override_deps: None,
        mock_token_service: MagicMock,
    ) -> None:
        @app.get("/test/no-auth")
        async def _test_no_auth(authed_user=Depends(get_current_user)):
            return {"ok": True}

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/test/no-auth")

        assert resp.status_code == 401
        body = resp.json()
        assert body["error"]["code"] == "UNAUTHORIZED"

    async def test_raises_401_on_non_bearer_header(
        self,
        override_deps: None,
        mock_token_service: MagicMock,
    ) -> None:
        @app.get("/test/bad-scheme")
        async def _test_bad(authed_user=Depends(get_current_user)):
            return {"ok": True}

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/test/bad-scheme", headers={"Authorization": "Basic xyz"})

        assert resp.status_code == 401

    async def test_raises_401_on_invalid_token(
        self,
        override_deps: None,
        mock_token_service: MagicMock,
    ) -> None:
        from features.auth.exceptions import InvalidTokenError

        mock_token_service.verify.side_effect = InvalidTokenError("bad token")

        @app.get("/test/bad-token")
        async def _test_bad_token(authed_user=Depends(get_current_user)):
            return {"ok": True}

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/test/bad-token", headers={"Authorization": "Bearer bad-token"})

        assert resp.status_code == 401
        body = resp.json()
        assert body["error"]["code"] == "INVALID_TOKEN"

    async def test_raises_401_on_deleted_user(
        self,
        override_deps: None,
        mock_token_service: MagicMock,
        mock_user_repo: MagicMock,
    ) -> None:
        payload = _make_payload()
        mock_token_service.verify.return_value = payload
        mock_user_repo.find_by_id.return_value = None

        @app.get("/test/gone")
        async def _test_gone(authed_user=Depends(get_current_user)):
            return {"ok": True}

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/test/gone", headers={"Authorization": "Bearer valid-token"})

        assert resp.status_code == 401
        body = resp.json()
        assert body["error"]["code"] == "UNAUTHORIZED"

    async def test_raises_403_on_inactive_user(
        self,
        override_deps: None,
        mock_token_service: MagicMock,
        mock_user_repo: MagicMock,
    ) -> None:
        user = _make_user()
        user.is_active = False
        payload = _make_payload(sub=str(user.id))
        mock_token_service.verify.return_value = payload
        mock_user_repo.find_by_id.return_value = user

        @app.get("/test/disabled")
        async def _test_disabled(authed_user=Depends(get_current_user)):
            return {"ok": True}

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/test/disabled", headers={"Authorization": "Bearer valid-token"})

        assert resp.status_code == 403
        body = resp.json()
        assert body["error"]["code"] == "FORBIDDEN"


class TestGetOptionalUser:
    async def test_returns_user_when_authenticated(
        self,
        override_deps: None,
        mock_token_service: MagicMock,
        mock_user_repo: MagicMock,
    ) -> None:
        user = _make_user()
        payload = _make_payload(sub=str(user.id))
        mock_token_service.verify.return_value = payload
        mock_user_repo.find_by_id.return_value = user

        @app.get("/test/optional-auth")
        async def _test_opt(authed_user=Depends(get_optional_user)):
            return {"ok": authed_user is not None, "email": authed_user.email if authed_user else None}

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/test/optional-auth", headers={"Authorization": "Bearer token"})

        assert resp.status_code == 200
        assert resp.json()["ok"] is True
        assert resp.json()["email"] == "alice@example.com"

    async def test_returns_none_without_header(
        self,
        override_deps: None,
        mock_token_service: MagicMock,
    ) -> None:
        @app.get("/test/no-header")
        async def _test_no_header(authed_user=Depends(get_optional_user)):
            return {"ok": authed_user is None}

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/test/no-header")

        assert resp.status_code == 200
        assert resp.json()["ok"] is True

    async def test_returns_none_with_invalid_token(
        self,
        override_deps: None,
        mock_token_service: MagicMock,
    ) -> None:
        from features.auth.exceptions import InvalidTokenError

        mock_token_service.verify.side_effect = InvalidTokenError("bad")

        @app.get("/test/opt-bad-token")
        async def _test_opt_bad(authed_user=Depends(get_optional_user)):
            return {"ok": authed_user is None}

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/test/opt-bad-token", headers={"Authorization": "Bearer bad"})

        assert resp.status_code == 200
        assert resp.json()["ok"] is True


class TestRoleChecker:
    async def test_passes_with_matching_role(
        self,
        override_deps: None,
        mock_token_service: MagicMock,
        mock_user_repo: MagicMock,
    ) -> None:
        user = _make_user()
        payload = _make_payload(sub=str(user.id), roles=["admin"])
        mock_token_service.verify.return_value = payload
        mock_user_repo.find_by_id.return_value = user

        @app.get("/test/admin-only")
        async def _test_admin(authed_user=Depends(RoleChecker("admin"))):
            return {"role": authed_user.roles[0]}

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/test/admin-only", headers={"Authorization": "Bearer t"})

        assert resp.status_code == 200
        assert resp.json()["role"] == "admin"

    async def test_raises_403_without_matching_role(
        self,
        override_deps: None,
        mock_token_service: MagicMock,
        mock_user_repo: MagicMock,
    ) -> None:
        user = _make_user()
        payload = _make_payload(sub=str(user.id), roles=["user"])
        mock_token_service.verify.return_value = payload
        mock_user_repo.find_by_id.return_value = user

        @app.get("/test/admin-only-403")
        async def _test_no_admin(authed_user=Depends(RoleChecker("admin"))):
            return {"ok": True}

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/test/admin-only-403", headers={"Authorization": "Bearer t"})

        assert resp.status_code == 403
        body = resp.json()
        assert body["error"]["code"] == "FORBIDDEN"

    async def test_passes_with_any_allowed_role(
        self,
        override_deps: None,
        mock_token_service: MagicMock,
        mock_user_repo: MagicMock,
    ) -> None:
        user = _make_user()
        payload = _make_payload(sub=str(user.id), roles=["moderator"])
        mock_token_service.verify.return_value = payload
        mock_user_repo.find_by_id.return_value = user

        @app.get("/test/multi-role")
        async def _test_multi(authed_user=Depends(RoleChecker("admin", "moderator"))):
            return {"role": authed_user.roles[0]}

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/test/multi-role", headers={"Authorization": "Bearer t"})

        assert resp.status_code == 200
        assert resp.json()["role"] == "moderator"


class TestPermissionChecker:
    async def test_passes_with_matching_permission(
        self,
        override_deps: None,
        mock_token_service: MagicMock,
        mock_user_repo: MagicMock,
    ) -> None:
        user = _make_user()
        payload = _make_payload(sub=str(user.id), permissions=["users:delete"])
        mock_token_service.verify.return_value = payload
        mock_user_repo.find_by_id.return_value = user

        @app.get("/test/perm-ok")
        async def _test_perm(authed_user=Depends(PermissionChecker("users:delete"))):
            return {"perm": authed_user.permissions[0]}

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/test/perm-ok", headers={"Authorization": "Bearer t"})

        assert resp.status_code == 200
        assert resp.json()["perm"] == "users:delete"

    async def test_raises_403_without_matching_permission(
        self,
        override_deps: None,
        mock_token_service: MagicMock,
        mock_user_repo: MagicMock,
    ) -> None:
        user = _make_user()
        payload = _make_payload(sub=str(user.id), permissions=[])
        mock_token_service.verify.return_value = payload
        mock_user_repo.find_by_id.return_value = user

        @app.get("/test/perm-403")
        async def _test_no_perm(authed_user=Depends(PermissionChecker("users:delete"))):
            return {"ok": True}

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/test/perm-403", headers={"Authorization": "Bearer t"})

        assert resp.status_code == 403
        body = resp.json()
        assert body["error"]["code"] == "FORBIDDEN"
