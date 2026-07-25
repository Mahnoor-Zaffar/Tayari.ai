"""User feature dependencies."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from features.users.service import UserService


async def get_user_service(
    db: AsyncSession = Depends(get_db),
) -> AsyncGenerator[UserService]:
    yield UserService(db)
