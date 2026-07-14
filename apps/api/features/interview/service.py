"""Interview service layer — business logic and orchestration.

The service:
    - Validates business rules (e.g. free-tier interview limits).
    - De-duplicates uploads by content hash.
    - Persists the configuration snapshot alongside the interview.
    - Returns Pydantic response models — never ORM instances or raw dicts.
"""

from __future__ import annotations

import hashlib
from uuid import UUID

from core.errors import ConflictError, NotFoundError, ValidationError
from features.interview.models import Interview as InterviewORM
from features.interview.repository import InterviewRepository
from features.interview.schemas import (
    CreateInterviewRequest,
    DeviceCheckRequest,
    DeviceCheckResponse,
    InterviewOptionsResponse,
    InterviewResponse,
    JobDescriptionResponse,
    ResumeResponse,
    UploadJobDescriptionRequest,
    UploadResumeRequest,
)

FREE_TIER_INTERVIEW_LIMIT = 1


class InterviewService:
    """Orchestrates interview setup operations.

    The repository is injected (DI) so tests can swap with a mock.
    """

    def __init__(self, repository: InterviewRepository) -> None:
        self._repo = repository

    # ── Create Interview ─────────────────────────────────────────────────

    async def create_interview(self, user_id: UUID, request: CreateInterviewRequest) -> InterviewResponse:
        """Validate the setup, persist configuration, and create the interview.

        Checks:
            - Free-tier users are limited to one interview (FR-05.1).
            - Referenced resume/JD belong to the user.
        """
        # Free-tier eligibility
        existing = await self._repo.count_user_interviews(user_id)
        if existing >= FREE_TIER_INTERVIEW_LIMIT:
            raise ConflictError("Free-tier limit reached. Upgrade to create more interviews.")

        # Validate resume ownership
        if request.resume_id:
            resume = await self._repo.get_resume_by_id(request.resume_id, user_id)
            if resume is None:
                raise ValidationError("Resume not found or does not belong to this user.")

        # Validate JD ownership
        if request.job_description_id:
            jd = await self._repo.get_job_description_by_id(request.job_description_id, user_id)
            if jd is None:
                raise ValidationError("Job description not found or does not belong to this user.")

        # Persist configuration snapshot
        config_data = {
            "user_id": user_id,
            "interview_type": request.type,
            "company": request.company,
            "role": request.role,
            "experience_level": request.experience_level,
            "language": request.language,
            "framework": request.framework,
            "difficulty": request.difficulty,
            "duration_minutes": request.duration_minutes,
            "custom_instructions": request.custom_instructions,
            "device_checks": request.device_checks,
        }
        config = await self._repo.create_configuration(config_data)

        # Create interview
        interview_data = {
            "user_id": user_id,
            "type": request.type,
            "company": request.company,
            "role": request.role,
            "experience_level": request.experience_level,
            "language": request.language,
            "framework": request.framework,
            "difficulty": request.difficulty,
            "duration_minutes": request.duration_minutes,
            "custom_instructions": request.custom_instructions,
            "resume_id": request.resume_id,
            "job_description_id": request.job_description_id,
            "template_id": request.template_id,
            "configuration_id": config.id,
            "timer_remaining": request.duration_minutes * 60,
            "status": "pending",
        }
        interview = await self._repo.create_interview(interview_data)

        return _interview_to_response(interview)

    # ── Options ───────────────────────────────────────────────────────────

    async def get_options(self) -> InterviewOptionsResponse:
        """Return all selectable options for the setup wizard."""
        await self._repo.list_active_templates()

        return InterviewOptionsResponse(
            interview_types=[
                {"value": "coding", "label": "Coding Interview"},
                {"value": "system-design", "label": "System Design"},
                {"value": "behavioral", "label": "Behavioral"},
            ],
            companies=_COMPANIES,
            roles=_ROLES,
            languages=[
                {"value": "python", "label": "Python"},
                {"value": "java", "label": "Java"},
                {"value": "cpp", "label": "C++"},
                {"value": "javascript", "label": "JavaScript"},
                {"value": "csharp", "label": "C#"},
            ],
            frameworks=[
                {"value": "react", "label": "React"},
                {"value": "vue", "label": "Vue"},
                {"value": "angular", "label": "Angular"},
                {"value": "svelte", "label": "Svelte"},
                {"value": "django", "label": "Django"},
                {"value": "fastapi", "label": "FastAPI"},
                {"value": "spring", "label": "Spring"},
                {"value": "express", "label": "Express"},
                {"value": "next", "label": "Next.js"},
            ],
            experience_levels=[
                {"value": "junior", "label": "Junior (0-3 years)"},
                {"value": "mid-senior", "label": "Mid/Senior (3-7 years)"},
                {"value": "staff-lead", "label": "Staff/Lead (7+ years)"},
            ],
            difficulties=[
                {"value": "easy", "label": "Easy"},
                {"value": "medium", "label": "Medium"},
                {"value": "hard", "label": "Hard"},
            ],
            durations=[
                {"value": "15", "label": "15 minutes"},
                {"value": "30", "label": "30 minutes"},
                {"value": "45", "label": "45 minutes"},
            ],
        )

    # ── Upload Resume ─────────────────────────────────────────────────────

    async def upload_resume(self, user_id: UUID, request: UploadResumeRequest) -> ResumeResponse:
        """Validate and store resume metadata.  De-duplicates by file hash.

        The actual file bytes are uploaded directly to S3/R2 via a presigned
        URL (Sprint 5+).  This endpoint only stores the metadata.
        """
        from features.interview.schemas import ALLOWED_MIME_RESUME

        if request.mime_type not in ALLOWED_MIME_RESUME:
            raise ValidationError(
                f"Unsupported file type: {request.mime_type}. Allowed: PDF, DOCX.",
            )

        existing = await self._repo.find_resume_by_hash(user_id, request.file_hash)
        if existing is not None:
            return ResumeResponse(
                id=existing.id,
                original_filename=existing.original_filename,
                mime_type=existing.mime_type,
                file_size=existing.file_size,
                file_hash=existing.file_hash,
                created_at=existing.created_at,
            )

        storage_path = f"uploads/{user_id}/resumes/{request.file_hash}"
        resume = await self._repo.create_resume(
            {
                "user_id": user_id,
                "original_filename": request.original_filename,
                "mime_type": request.mime_type,
                "file_size": request.file_size,
                "storage_path": storage_path,
                "file_hash": request.file_hash,
            }
        )

        return ResumeResponse(
            id=resume.id,
            original_filename=resume.original_filename,
            mime_type=resume.mime_type,
            file_size=resume.file_size,
            file_hash=resume.file_hash,
            created_at=resume.created_at,
        )

    # ── Upload Job Description ────────────────────────────────────────────

    async def upload_job_description(
        self, user_id: UUID, request: UploadJobDescriptionRequest
    ) -> JobDescriptionResponse:
        """Accept raw text or file-based JD.  De-duplicates files by hash."""
        from features.interview.schemas import ALLOWED_MIME_JD

        if request.source == "text":
            jd = await self._repo.create_job_description(
                {
                    "user_id": user_id,
                    "source": "text",
                    "raw_content": request.raw_text,
                    "mime_type": "text/plain",
                    "file_hash": hashlib.sha256(request.raw_text.encode()).hexdigest(),
                }
            )
        else:
            if request.mime_type and request.mime_type not in ALLOWED_MIME_JD:
                raise ValidationError(
                    f"Unsupported file type: {request.mime_type}. Allowed: PDF, TXT, DOCX.",
                )

            existing = await self._repo.find_job_description_by_hash(user_id, request.file_hash)
            if existing is not None:
                return JobDescriptionResponse(
                    id=existing.id,
                    source=existing.source,
                    original_filename=existing.original_filename,
                    created_at=existing.created_at,
                )

            storage_path = f"uploads/{user_id}/job-descriptions/{request.file_hash}"
            jd = await self._repo.create_job_description(
                {
                    "user_id": user_id,
                    "source": "file",
                    "original_filename": request.original_filename,
                    "mime_type": request.mime_type,
                    "file_size": request.file_size,
                    "storage_path": storage_path,
                    "file_hash": request.file_hash,
                    "raw_content": "",
                }
            )

        return JobDescriptionResponse(
            id=jd.id,
            source=jd.source,
            original_filename=jd.original_filename,
            created_at=jd.created_at,
        )

    # ── Device Check ─────────────────────────────────────────────────────

    async def device_check(self, request: DeviceCheckRequest) -> DeviceCheckResponse:
        """Validate device capabilities.

        This is a server-side log + validation.  The actual checks happen
        client-side (MediaDevices API).  The server validates the payload
        and returns the aggregate result.

        Microphone and browser compatibility are required.  Camera is
        optional (for future video interview type).
        """
        all_passed = request.microphone and request.browser and request.speaker

        return DeviceCheckResponse(
            microphone=request.microphone,
            camera=request.camera,
            speaker=request.speaker,
            browser=request.browser,
            all_passed=all_passed,
        )

    # ── List & Get ───────────────────────────────────────────────────────

    async def list_interviews(self, user_id: UUID, limit: int = 20, offset: int = 0) -> list[InterviewResponse]:
        """Return paginated interview history for a user."""
        interviews = await self._repo.list_interviews(user_id, limit, offset)
        return [_interview_to_response(i) for i in interviews]

    async def get_interview(self, interview_id: UUID, user_id: UUID) -> InterviewResponse:
        """Return a single interview by ID, scoped to the user."""
        interview = await self._repo.get_interview_by_id(interview_id, user_id)
        if interview is None:
            raise NotFoundError("Interview not found")
        return _interview_to_response(interview)


# ── Helpers ─────────────────────────────────────────────────────────────────


def _interview_to_response(interview: InterviewORM) -> InterviewResponse:
    return InterviewResponse(
        id=interview.id,
        type=interview.type,
        company=interview.company,
        role=interview.role,
        experience_level=interview.experience_level,
        language=interview.language,
        framework=interview.framework,
        difficulty=interview.difficulty,
        duration_minutes=interview.duration_minutes,
        custom_instructions=interview.custom_instructions,
        status=interview.status,
        timer_remaining=interview.timer_remaining,
        resume_id=interview.resume_id,
        job_description_id=interview.job_description_id,
        template_id=interview.template_id,
        created_at=interview.created_at,
    )


# ── Static option data (will be replaced by DB tables when seeded) ──────────

_COMPANIES = [
    "Google",
    "Meta",
    "Amazon",
    "Apple",
    "Microsoft",
    "Netflix",
    "Tesla",
    "Stripe",
    "Airbnb",
    "Uber",
    "Lyft",
    "Spotify",
    "Adobe",
    "Salesforce",
    "Oracle",
    "IBM",
    "Intel",
    "Nvidia",
    "Samsung",
    "Twitter",
    "LinkedIn",
    "Slack",
    "Square",
    "Palantir",
    "Snowflake",
    "Datadog",
    "HashiCorp",
    "Stripe",
    "Databricks",
    "Riot Games",
    "ByteDance",
    "TikTok",
    "Snap",
    "Pinterest",
    "Reddit",
]

_ROLES = [
    "Software Engineer",
    "Senior Software Engineer",
    "Staff Software Engineer",
    "Frontend Engineer",
    "Backend Engineer",
    "Full-Stack Engineer",
    "DevOps Engineer",
    "Site Reliability Engineer",
    "Machine Learning Engineer",
    "Data Engineer",
    "Security Engineer",
    "Engineering Manager",
    "Technical Lead",
    "Principal Engineer",
]
