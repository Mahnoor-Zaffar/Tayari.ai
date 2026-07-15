"""Code execution dependency injection."""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from features.code.repository import CodeRepository
from features.code.service import CodeExecutionService


async def get_code_service(
    db: AsyncSession = Depends(get_db),
) -> CodeExecutionService:
    repo = CodeRepository(db)
    return CodeExecutionService(repo)
