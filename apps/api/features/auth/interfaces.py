from datetime import datetime
from typing import Protocol
from uuid import UUID

from features.auth.domain.user import User, UserCreate, UserUpdate
from features.auth.jwt.models import TokenPayload


class UserRepositoryProtocol(Protocol):
    """Data-access contract the service depends on."""

    async def find_by_email(self, email: str, *, include_deleted: bool = False) -> User | None: ...

    async def find_by_id(self, user_id: UUID, *, include_deleted: bool = False) -> User | None: ...

    async def create_user(self, data: UserCreate) -> User: ...

    async def update_user(self, user_id: UUID, data: UserUpdate) -> User: ...

    async def exists(
        self, *, email: str | None = None, username: str | None = None, include_deleted: bool = False
    ) -> bool: ...


class PasswordServiceProtocol(Protocol):
    """Password hashing, verification and staleness-detection contract.

    Implementations must never expose raw hashes to callers — only accept
    them for verification.
    """

    def hash_password(self, password: str) -> str: ...

    def verify_password(self, password: str, password_hash: str) -> bool: ...

    def needs_rehash(self, password_hash: str) -> bool: ...


class TokenServiceProtocol(Protocol):
    """Token lifecycle contract for access, refresh, verification, and reset tokens.

    Extensible to OAuth2 flows: claims carry ``iss``/``aud`` for multi-service
    scoping, and the verify step enforces audience + issuer matching.
    """

    def create_access_token(
        self,
        user_id: UUID,
        roles: list[str] | None = None,
        permissions: list[str] | None = None,
    ) -> str: ...

    def create_refresh_token(self, user_id: UUID, token_family: str | None = None) -> str: ...

    def create_email_verification_token(self, user_id: UUID) -> str: ...

    def create_password_reset_token(self, user_id: UUID) -> str: ...

    async def verify(self, token: str, expected_type: str) -> TokenPayload: ...

    async def revoke(self, token: str) -> None: ...

    async def revoke_family(self, token_family: str, expires_at: datetime) -> None: ...

    def peek(self, token: str) -> dict: ...
