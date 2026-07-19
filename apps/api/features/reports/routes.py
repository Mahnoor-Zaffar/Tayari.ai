"""Evaluation API routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from core.errors import success_response
from features.auth.guard import CurrentUser, get_current_user
from features.reports.dependencies import get_evaluation_service
from features.reports.service import EvaluationService

router = APIRouter(prefix="/evaluations", tags=["evaluations"])


@router.post("/{interview_id}", status_code=201, summary="Evaluate an interview")
async def evaluate_interview(
    interview_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    service: EvaluationService = Depends(get_evaluation_service),
) -> dict:
    result = await service.evaluate_interview(interview_id, current_user.id)
    return success_response(result)


@router.get("", summary="List all evaluations")
async def list_evaluations(
    current_user: CurrentUser = Depends(get_current_user),
    service: EvaluationService = Depends(get_evaluation_service),
) -> dict:
    result = await service.list_evaluations(current_user.id)
    return success_response({"evaluations": result})


@router.get("/{interview_id}", summary="Get evaluation result")
async def get_evaluation(
    interview_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    service: EvaluationService = Depends(get_evaluation_service),
) -> dict:
    result = await service.get_evaluation(interview_id)
    if result is None:
        from core.errors import NotFoundError
        raise NotFoundError("Evaluation not found")
    return success_response(result)
