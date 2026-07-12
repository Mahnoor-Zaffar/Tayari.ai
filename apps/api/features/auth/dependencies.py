from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import get_db
from features.auth.jwt.config import JWTConfig
from features.auth.jwt.jti_blacklist import MemoryBlacklist
from features.auth.jwt.service import TokenService
from features.auth.password.service import PasswordService
from features.auth.repositories import UserRepository
from features.auth.services import AuthenticationService

_password_service = PasswordService()
_jwt_config = JWTConfig(
    SECRET_KEY=settings.JWT_SECRET_KEY,
    ALGORITHM=settings.JWT_ALGORITHM,
    ACCESS_TOKEN_TTL=settings.jwt_access_token_ttl,
    REFRESH_TOKEN_TTL=settings.jwt_refresh_token_ttl,
    EMAIL_VERIFY_TTL=settings.jwt_email_verify_ttl,
    PASSWORD_RESET_TTL=settings.jwt_password_reset_ttl,
)
_blacklist = MemoryBlacklist()
_token_service = TokenService(config=_jwt_config, blacklist=_blacklist)


async def get_auth_service(
    db: AsyncSession = Depends(get_db),
) -> AuthenticationService:
    repository = UserRepository(db)
    return AuthenticationService(
        repository=repository,
        password_service=_password_service,
        token_service=_token_service,
    )


async def get_token_service() -> TokenService:
    return _token_service
