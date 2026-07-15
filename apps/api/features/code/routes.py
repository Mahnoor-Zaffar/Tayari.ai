"""Code execution API routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from core.errors import success_response
from features.auth.guard import CurrentUser, get_current_user
from features.code.dependencies import get_code_service
from features.code.schemas import RunCodeRequest, SubmitCodeRequest
from features.code.service import CodeExecutionService

router = APIRouter(prefix="/code", tags=["code"])


@router.post("/run", summary="Execute code once", description="Run source code against a single test input and return the output.")
async def run_code(
    request: RunCodeRequest,
    service: CodeExecutionService = Depends(get_code_service),
) -> dict:
    try:
        result = await service.run_code(request.language, request.source_code, request.test_input)
        return success_response(result.model_dump())
    except ValueError as exc:
        from core.errors import ValidationError
        raise ValidationError(str(exc))


@router.post("/submit", status_code=201, summary="Submit code for evaluation", description="Submit source code for full test suite execution. Results are persisted.")
async def submit_code(
    request: SubmitCodeRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: CodeExecutionService = Depends(get_code_service),
) -> dict:
    result = await service.submit_code(
        interview_id=request.interview_id,
        user_id=current_user.id,
        language=request.language,
        source_code=request.source_code,
        test_inputs=request.test_inputs,
    )
    return success_response(result)


@router.get("/result/{submission_id}", summary="Get submission result", description="Return the result of a code submission by ID.")
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


@router.get("/languages", summary="List supported languages", description="Return all supported programming languages and their metadata.")
async def list_languages(
    service: CodeExecutionService = Depends(get_code_service),
) -> dict:
    return success_response({"languages": service.get_languages()})
