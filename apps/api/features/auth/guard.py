from uuid import UUID

from fastapi import Depends, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.errors import AppError, ErrorCode
from features.auth.dependencies import get_token_service
from features.auth.exceptions import InvalidTokenError
from features.auth.jwt.service import TokenService
from features.auth.repositories import UserRepository


class CurrentUser(BaseModel):
    """Authenticated user combined from the database record and JWT claims.

    Returned by ``get_current_user`` — the primary dependency for protected
    routes.  Excludes sensitive fields like ``password_hash`` and
    ``deleted_at`` that exist on the domain ``User`` model.
    """

    id: UUID
    email: str
    username: str
    display_name: str
    email_verified: bool
    is_active: bool
    roles: list[str]
    permissions: list[str]


# ── Primary dependency ──────────────────────────────────────────────────────


async def get_current_user(
    request: Request,
    token_service: TokenService = Depends(get_token_service),
    db: AsyncSession = Depends(get_db),
) -> CurrentUser:
    """Extract and validate the ``Authorization: Bearer <access_token>``
    header, look up the user in the database, and return a ``CurrentUser``.

    Raises ``AppError``:
    * 401 when the header is missing or malformed.
    * 401 when the token is expired, revoked, or signed by a different key.
    * 403 when the user account is disabled.
    * 401 when the user has been deleted (token valid, record gone).
    """
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise AppError(
            ErrorCode.UNAUTHORIZED,
            "Missing or invalid Authorization header",
            status.HTTP_401_UNAUTHORIZED,
        )

    token = auth.removeprefix("Bearer ")
    try:
        payload = await token_service.verify(token, "access")
    except InvalidTokenError:
        raise AppError(
            ErrorCode.INVALID_TOKEN,
            "Invalid or expired access token",
            status.HTTP_401_UNAUTHORIZED,
        )

    repo = UserRepository(db)
    user = await repo.find_by_id(UUID(payload.sub))

    if user is None:
        raise AppError(
            ErrorCode.UNAUTHORIZED,
            "User not found",
            status.HTTP_401_UNAUTHORIZED,
        )

    if not user.is_active:
        raise AppError(
            ErrorCode.FORBIDDEN,
            "Account is disabled",
            status.HTTP_403_FORBIDDEN,
        )

    return CurrentUser(
        id=user.id,
        email=user.email,
        username=user.username,
        display_name=user.display_name,
        email_verified=user.email_verified,
        is_active=user.is_active,
        roles=payload.roles,
        permissions=payload.permissions,
    )


# ── Optional variant ────────────────────────────────────────────────────────


async def get_optional_user(
    request: Request,
    token_service: TokenService = Depends(get_token_service),
    db: AsyncSession = Depends(get_db),
) -> CurrentUser | None:
    """Like ``get_current_user`` but returns ``None`` instead of raising
    when no valid token is provided.

    Useful for routes that behave differently for authenticated vs.
    anonymous users (e.g. read public data + personalise if logged in).
    """
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None

    token = auth.removeprefix("Bearer ")
    try:
        payload = await token_service.verify(token, "access")
    except InvalidTokenError:
        return None

    repo = UserRepository(db)
    user = await repo.find_by_id(UUID(payload.sub))

    if user is None or not user.is_active:
        return None

    return CurrentUser(
        id=user.id,
        email=user.email,
        username=user.username,
        display_name=user.display_name,
        email_verified=user.email_verified,
        is_active=user.is_active,
        roles=payload.roles,
        permissions=payload.permissions,
    )


# ── Route guards (callable classes) ─────────────────────────────────────────


class RoleChecker:
    """FastAPI dependency guard that verifies the current user has at least
    one of the given roles.

    Usage::

        @router.get("/admin/dashboard")
        async def dashboard(
            current_user: CurrentUser = Depends(RoleChecker("admin", "superuser")),
        ) -> dict: ...

    Raises 403 ``FORBIDDEN`` when none of the required roles are present.
    """

    def __init__(self, *allowed: str) -> None:
        self._allowed = allowed

    async def __call__(self, current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not set(self._allowed) & set(current_user.roles):
            raise AppError(
                ErrorCode.FORBIDDEN,
                f"Requires one of: {', '.join(self._allowed)}",
                status.HTTP_403_FORBIDDEN,
            )
        return current_user


class PermissionChecker:
    """FastAPI dependency guard that verifies the current user has at least
    one of the given permissions.

    Usage::

        @router.delete("/users/{user_id}")
        async def delete_user(
            current_user: CurrentUser = Depends(PermissionChecker("users:delete")),
        ) -> dict: ...

    Raises 403 ``FORBIDDEN`` when none of the required permissions are present.
    """

    def __init__(self, *required: str) -> None:
        self._required = required

    async def __call__(self, current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not set(self._required) & set(current_user.permissions):
            raise AppError(
                ErrorCode.FORBIDDEN,
                f"Requires one of: {', '.join(self._required)}",
                status.HTTP_403_FORBIDDEN,
            )
        return current_user
