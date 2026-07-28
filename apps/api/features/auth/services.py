from uuid import UUID

from pydantic import BaseModel

from core.config import settings
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
from features.email.service import send_reset_email, send_verification_email


def _get_admin_emails() -> frozenset[str]:
    """Return admin emails from settings, falling back to the default."""
    raw = settings.ADMIN_EMAILS or "admin@tayari.ai"
    return frozenset(email.strip().lower() for email in raw.split(",") if email.strip())


def _user_roles(email: str) -> tuple[list[str], list[str]]:
    """Return (roles, permissions) for a user based on their email."""
    if email.lower() in _get_admin_emails():
        return (["admin", "user"], ["users:read", "users:write", "users:delete"])
    return (["user"], [])


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
    """Orchestrates authentication workflows."""

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

        roles, permissions = _user_roles(data.email)

        verify_token = self._tokens.create_email_verification_token(user.id)
        verify_url = f"{settings.FRONTEND_URL}/auth/verify-email?token={verify_token}"
        send_verification_email(to=user.email, verify_url=verify_url)

        return AuthResult(
            user=user,
            access_token=self._tokens.create_access_token(user.id, roles=roles, permissions=permissions),
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

        roles, permissions = _user_roles(email)
        return AuthResult(
            user=user,
            access_token=self._tokens.create_access_token(user.id, roles=roles, permissions=permissions),
            refresh_token=self._tokens.create_refresh_token(user.id),
        )

    async def social_login(self, provider: str, access_token: str) -> AuthResult:
        """Sign in or register via Supabase social login (Google, GitHub)."""
        if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
            raise InvalidCredentialsError("Social login is not configured")

        import httpx

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{settings.SUPABASE_URL}/auth/v1/user",
                headers={
                    "apikey": settings.SUPABASE_SERVICE_KEY,
                    "Authorization": f"Bearer {access_token}",
                },
                timeout=10,
            )
            if resp.status_code != 200:
                raise InvalidCredentialsError("Invalid social login token")

            user_data = resp.json()
            email = (user_data.get("email") or "").lower()
            if not email:
                raise InvalidCredentialsError("Email not provided by provider")

            display_name = (
                user_data.get("user_metadata", {}).get("full_name")
                or user_data.get("user_metadata", {}).get("name")
                or email.split("@")[0]
            )

        existing = await self._repository.find_by_email(email)
        if existing is not None:
            if not existing.is_active:
                raise UserNotActiveError("Account is disabled")
            roles, permissions = _user_roles(email)
            return AuthResult(
                user=existing,
                access_token=self._tokens.create_access_token(existing.id, roles=roles, permissions=permissions),
                refresh_token=self._tokens.create_refresh_token(existing.id),
            )

        # Create new user
        import secrets

        username = email.split("@")[0][:50]
        while await self._repository.exists(username=username):
            username = f"{email.split('@')[0][:45]}_{secrets.token_hex(2)}"

        from passlib.hash import bcrypt

        user = await self._repository.create_user(
            UserCreate(
                email=email,
                username=username,
                display_name=display_name[:100],
                password_hash=bcrypt.hash(secrets.token_urlsafe(32)),
            )
        )

        roles, permissions = _user_roles(email)
        return AuthResult(
            user=user,
            access_token=self._tokens.create_access_token(user.id, roles=roles, permissions=permissions),
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
        await self._tokens.revoke(refresh_token)

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
        reset_url = f"{settings.FRONTEND_URL}/auth/reset-password?token={reset_token}"
        send_reset_email(to=user.email, reset_url=reset_url)

    async def reset_password(self, token: str, new_password: str) -> None:
        """Verify a password‑reset token and update the user's password hash."""
        payload = await self._tokens.verify(token, "password_reset")

        user_id = UUID(payload.sub)
        user = await self._repository.find_by_id(user_id, include_deleted=True)

        if user is None:
            raise UserNotFoundError("User not found")

        if not user.is_active or user.deleted_at is not None:
            raise UserNotActiveError("Account is disabled or deleted")

        new_hash = self._password.hash_password(new_password)
        await self._repository.update_user(user_id, UserUpdate(password_hash=new_hash))
