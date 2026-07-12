from uuid import UUID

from pydantic import BaseModel

from features.auth.domain.user import User, UserCreate, UserUpdate
from features.auth.exceptions import (
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    UsernameAlreadyExistsError,
    UserNotActiveError,
    UserNotFoundError,
)
from features.auth.interfaces import (
    PasswordServiceProtocol,
    TokenServiceProtocol,
    UserRepositoryProtocol,
)

# ── Service-level models ───────────────────────────────────────────────────


class AuthResult(BaseModel):
    """Structured return value for login, register, and refresh."""

    user: User
    access_token: str
    refresh_token: str


class RegistrationData(BaseModel):
    """Plain-text registration input (password is not yet hashed)."""

    email: str
    username: str
    display_name: str
    password: str


# ── AuthenticationService ──────────────────────────────────────────────────


class AuthenticationService:
    """Orchestrates authentication workflows.

    Delegates persistence to ``repository``, password operations to
    ``password_service``, and token operations to ``token_service``.
    Contains zero database or HTTP logic — only business rules.
    """

    def __init__(
        self,
        repository: UserRepositoryProtocol,
        password_service: PasswordServiceProtocol,
        token_service: TokenServiceProtocol,
    ) -> None:
        self._repository = repository
        self._password = password_service
        self._tokens = token_service

    async def register(self, data: RegistrationData) -> AuthResult:
        if await self._repository.exists(email=data.email):
            raise EmailAlreadyExistsError(f"Email '{data.email}' is already registered")

        if await self._repository.exists(username=data.username):
            raise UsernameAlreadyExistsError(f"Username '{data.username}' is already taken")

        password_hash = self._password.hash_password(data.password)
        user = await self._repository.create_user(
            UserCreate(
                email=data.email,
                username=data.username,
                display_name=data.display_name,
                password_hash=password_hash,
            )
        )

        return AuthResult(
            user=user,
            access_token=self._tokens.create_access_token(user.id, roles=["user"], permissions=[]),
            refresh_token=self._tokens.create_refresh_token(user.id),
        )

    async def login(self, email: str, password: str) -> AuthResult:
        user = await self._repository.find_by_email(email)

        if user is None:
            raise InvalidCredentialsError("Invalid email or password")

        if not self._password.verify_password(password, user.password_hash):
            raise InvalidCredentialsError("Invalid email or password")

        if not user.is_active:
            raise UserNotActiveError("Account is disabled or deleted")

        return AuthResult(
            user=user,
            access_token=self._tokens.create_access_token(user.id, roles=["user"], permissions=[]),
            refresh_token=self._tokens.create_refresh_token(user.id),
        )

    async def refresh(self, refresh_token: str) -> AuthResult:
        payload = await self._tokens.verify(refresh_token, "refresh")

        # Rotation: revoke old token before issuing new ones
        await self._tokens.revoke(refresh_token)

        user_id = UUID(payload.sub)
        user = await self._repository.find_by_id(user_id, include_deleted=True)

        if user is None:
            raise UserNotFoundError("User not found")

        if not user.is_active or user.deleted_at is not None:
            raise UserNotActiveError("Account is disabled or deleted")

        return AuthResult(
            user=user,
            access_token=self._tokens.create_access_token(
                user.id, roles=payload.roles, permissions=payload.permissions
            ),
            refresh_token=self._tokens.create_refresh_token(user.id, token_family=payload.token_family),
        )

    async def logout(self, refresh_token: str) -> None:
        await self._tokens.verify(refresh_token, "refresh")

    async def verify_email(self, token: str) -> None:
        payload = await self._tokens.verify(token, "email_verify")

        user_id = UUID(payload.sub)
        user = await self._repository.find_by_id(user_id, include_deleted=True)

        if user is None:
            raise UserNotFoundError("User not found")

        await self._repository.update_user(user_id, UserUpdate(email_verified=True))

    async def forgot_password(self, email: str) -> None:
        """Always succeeds from the caller's perspective (prevents email enumeration)."""
        user = await self._repository.find_by_email(email)

        if user is None or user.deleted_at is not None:
            return

        reset_token = self._tokens.create_password_reset_token(user.id)
        _ = reset_token  # TODO: send via email using RESEND_API_KEY
