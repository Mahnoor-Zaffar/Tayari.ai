from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import get_db
from core.rate_limit import InMemoryRateLimiter, RedisRateLimiter, rate_limiter
from features.auth.jwt.config import JWTConfig
from features.auth.jwt.jti_blacklist import MemoryBlacklist
from features.auth.jwt.redis_blacklist import RedisBlacklist
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


# Blacklist backend selection:
#   - Production: always Redis-backed (revocation must survive process restarts
#     and be shared across workers) — a local hostname is not a reason to
#     downgrade to per-process memory.
#   - Non-production: Redis when a non-local Redis is configured, otherwise the
#     in-memory blacklist for tests / local dev without a Redis instance.
def _select_blacklist() -> RedisBlacklist | MemoryBlacklist:
    if settings.is_production:
        return RedisBlacklist()
    if settings.REDIS_URL and not settings.REDIS_URL.startswith("redis://localhost"):
        return RedisBlacklist()
    return MemoryBlacklist()


_blacklist = _select_blacklist()
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


def get_rate_limiter() -> RedisRateLimiter | InMemoryRateLimiter:
    """Return the shared login rate limiter (Redis-backed in production)."""
    return rate_limiter
