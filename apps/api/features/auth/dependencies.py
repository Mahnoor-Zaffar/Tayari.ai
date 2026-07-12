from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from features.auth.jwt.config import JWTConfig
from features.auth.jwt.service import TokenService
from features.auth.password.service import PasswordService
from features.auth.repositories import UserRepository
from features.auth.services import AuthenticationService

_password_service = PasswordService()
_token_service = TokenService(config=JWTConfig())


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
