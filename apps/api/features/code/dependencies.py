"""Code execution dependency injection."""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from features.code.repository import CodeRepository
from features.code.service import CodeExecutionService
from judge.queue import ExecutionQueue

_execution_queue: ExecutionQueue | None = None


def get_execution_queue() -> ExecutionQueue:
    global _execution_queue
    if _execution_queue is None:
        _execution_queue = ExecutionQueue(max_concurrent=5)
    return _execution_queue


async def get_code_service(
    db: AsyncSession = Depends(get_db),
) -> CodeExecutionService:
    repo = CodeRepository(db)
    queue = get_execution_queue()
    return CodeExecutionService(repo=repo, queue=queue)
