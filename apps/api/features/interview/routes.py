"""Interview API routes.

All business logic is delegated to ``InterviewService`` — routes contain
no business logic, only HTTP wiring.

Endpoints:
    POST   /interviews                  — Create interview from setup wizard
    GET    /interviews/options           — Return all selectable options
    POST   /interviews/upload-resume     — Upload resume metadata
    POST   /interviews/upload-job-description — Upload JD (text or file)
    POST   /interviews/device-check      — Validate device capabilities
    GET    /interviews                   — List user's interviews
    GET    /interviews/{interview_id}    — Fetch single interview
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from core.errors import success_response
from features.auth.guard import CurrentUser, get_current_user
from features.interview.dependencies import get_interview_service
from features.interview.schemas import (
    CreateInterviewRequest,
    DeviceCheckRequest,
    UploadJobDescriptionRequest,
    UploadResumeRequest,
)
from features.interview.service import InterviewService

router = APIRouter(tags=["interviews"])


# ── Create ──────────────────────────────────────────────────────────────────


@router.post(
    "/interviews",
    status_code=201,
    summary="Create interview configuration",
    description="Create a new interview from the setup wizard configuration.",
)
async def create_interview(
    request: CreateInterviewRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: InterviewService = Depends(get_interview_service),
) -> dict:
    result = await service.create_interview(current_user.id, request)
    return success_response(result.model_dump(mode="json"))


# ── Options ─────────────────────────────────────────────────────────────────


@router.get(
    "/interviews/options",
    summary="Get interview setup options",
    description="Return companies, roles, languages, frameworks, experience levels, durations, "
    "difficulties, and interview types for the setup wizard.",
)
async def get_interview_options(
    current_user: CurrentUser = Depends(get_current_user),
    service: InterviewService = Depends(get_interview_service),
) -> dict:
    result = await service.get_options()
    return success_response(result.model_dump(mode="json"))


# ── Upload Resume ────────────────────────────────────────────────────────────


@router.post(
    "/interviews/upload-resume",
    status_code=201,
    summary="Upload resume metadata",
    description="Validate and store resume file metadata.  De-duplicates by content hash.",
)
async def upload_resume(
    request: UploadResumeRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: InterviewService = Depends(get_interview_service),
) -> dict:
    result = await service.upload_resume(current_user.id, request)
    return success_response(result.model_dump(mode="json"))


# ── Upload Job Description ──────────────────────────────────────────────────


@router.post(
    "/interviews/upload-job-description",
    status_code=201,
    summary="Upload job description",
    description="Accept raw text, PDF, or DOCX job description.  Stores parsed content.",
)
async def upload_job_description(
    request: UploadJobDescriptionRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: InterviewService = Depends(get_interview_service),
) -> dict:
    result = await service.upload_job_description(current_user.id, request)
    return success_response(result.model_dump(mode="json"))


# ── Device Check ────────────────────────────────────────────────────────────


@router.post(
    "/interviews/device-check",
    summary="Validate device compatibility",
    description="Validate microphone, camera, speaker, and browser support for interviews.",
)
async def device_check(
    request: DeviceCheckRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: InterviewService = Depends(get_interview_service),
) -> dict:
    result = await service.device_check(request)
    return success_response(result.model_dump(mode="json"))


# ── List Interviews ─────────────────────────────────────────────────────────


@router.get(
    "/interviews",
    summary="List user interviews",
    description="Return paginated interview history for the authenticated user.",
)
async def list_interviews(
    current_user: CurrentUser = Depends(get_current_user),
    service: InterviewService = Depends(get_interview_service),
    limit: int = 20,
    offset: int = 0,
) -> dict:
    """List the current user's interviews."""
    interviews = await service.list_interviews(current_user.id, limit, offset)
    data = [i.model_dump(mode="json") for i in interviews]
    return success_response({"interviews": data})


# ── Get Single Interview ────────────────────────────────────────────────────


@router.get(
    "/interviews/{interview_id}",
    summary="Get interview details",
    description="Return a single interview by ID, scoped to the authenticated user.",
)
async def get_interview(
    interview_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    service: InterviewService = Depends(get_interview_service),
) -> dict:
    """Fetch a single interview."""
    result = await service.get_interview(interview_id, current_user.id)
    return success_response(result.model_dump(mode="json"))
