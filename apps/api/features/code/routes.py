"""Code execution API routes.

Rate limiting:
    - ``/code/run``: max 10 requests per minute per user
    - ``/code/submit``: max 5 submissions per minute per user
"""

from __future__ import annotations

import time
from collections import defaultdict
from uuid import UUID

from fastapi import APIRouter, Depends, Request

from core.errors import success_response
from features.auth.guard import CurrentUser, get_current_user
from features.code.dependencies import get_code_service
from features.code.schemas import RunCodeRequest, SubmitCodeRequest
from features.code.service import CodeExecutionService

router = APIRouter(prefix="/code", tags=["code"])


RATE_LIMIT_WINDOW_S = 60

_rate_limits: dict[str, list[float]] = defaultdict(list)


def _check_rate_limit(key: str, max_per_window: int) -> None:
    """Raise 429 if rate limit exceeded."""
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW_S
    timestamps = _rate_limits[key]
    _rate_limits[key] = [t for t in timestamps if t > window_start]
    if len(_rate_limits[key]) >= max_per_window:
        from fastapi import HTTPException
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Please slow down.")
    _rate_limits[key].append(now)


@router.post("/run", summary="Execute code once")
async def run_code(
    request: RunCodeRequest,
    req: Request,
    service: CodeExecutionService = Depends(get_code_service),
) -> dict:
    client_key = req.client.host if req.client else "unknown"
    _check_rate_limit(f"run:{client_key}", 10)
    try:
        result = await service.run_code(request.language, request.source_code, request.test_input)
        return success_response(result.model_dump())
    except ValueError as exc:
        from core.errors import ValidationError
        raise ValidationError(str(exc))


@router.post("/submit", status_code=201, summary="Submit code for evaluation")
async def submit_code(
    request: SubmitCodeRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: CodeExecutionService = Depends(get_code_service),
) -> dict:
    _check_rate_limit(f"submit:{current_user.id}", 5)
    result = await service.submit_code(
        interview_id=request.interview_id,
        user_id=current_user.id,
        language=request.language,
        source_code=request.source_code,
        test_inputs=request.test_inputs,
    )
    return success_response(result)


@router.get("/result/{submission_id}", summary="Get submission result")
async def get_submission_result(
    submission_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    service: CodeExecutionService = Depends(get_code_service),
) -> dict:
    result = await service.get_submission_result(submission_id, current_user.id)
    if result is None:
        from core.errors import NotFoundError
        raise NotFoundError("Submission not found")
    return success_response(result)


@router.get("/languages", summary="List supported languages")
async def list_languages(
    service: CodeExecutionService = Depends(get_code_service),
) -> dict:
    return success_response({"languages": service.get_languages()})
