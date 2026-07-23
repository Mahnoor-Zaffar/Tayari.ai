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
    AnalyzeJdResponse,
    ConfigValidationWarning,
    CreateInterviewRequest,
    CreateTemplateRequest,
    DeviceCheckRequest,
    DeviceCheckResponse,
    DifficultyEstimateResponse,
    InterviewOptionsResponse,
    InterviewResponse,
    JobDescriptionResponse,
    ParsedSkill,
    ParseResumeResponse,
    ResumeResponse,
    TemplateResponse,
    UploadJobDescriptionRequest,
    UploadResumeRequest,
    ValidateConfigResponse,
)

FREE_TIER_INTERVIEW_LIMIT = 10


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
            - Duplicate pending interview guard (same config within 2 minutes).
        """
        # Duplicate guard: if a pending interview with the same config was
        # created in the last 2 minutes, return it instead of creating another.
        duplicate = await self._repo.find_pending_duplicate(
            user_id=user_id,
            interview_type=request.type,
            company=request.company,
            role=request.role,
            experience_level=request.experience_level,
            language=request.language,
            difficulty=request.difficulty,
            duration_minutes=request.duration_minutes,
            seconds_window=120,
        )
        if duplicate is not None:
            return _interview_to_response(duplicate)

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
            "spoken_language": request.spoken_language,
            "framework": request.framework,
            "difficulty": request.difficulty,
            "duration_minutes": request.duration_minutes,
            "custom_instructions": request.custom_instructions,
            "system_design_problem": request.system_design_problem,
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
            "spoken_language": request.spoken_language,
            "framework": request.framework,
            "difficulty": request.difficulty,
            "duration_minutes": request.duration_minutes,
            "custom_instructions": request.custom_instructions,
            "system_design_problem": request.system_design_problem,
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

    # ── Templates ────────────────────────────────────────────────────────

    async def create_user_template(self, user_id: UUID, request: CreateTemplateRequest) -> TemplateResponse:
        """Save the current interview configuration as a reusable template."""
        data = {
            "user_id": user_id,
            "name": request.name,
            "description": request.description,
            "interview_type": request.interview_type,
            "company": request.company,
            "role": request.role,
            "experience_level": request.experience_level,
            "language": request.language,
            "framework": request.framework,
            "difficulty": request.difficulty,
            "duration_minutes": request.duration_minutes,
            "custom_instructions": request.custom_instructions,
            "system_design_problem": request.system_design_problem,
            "resume_id": request.resume_id,
            "job_description_id": request.job_description_id,
        }
        template = await self._repo.create_user_template(data)
        return _template_to_response(template)

    async def list_user_templates(self, user_id: UUID) -> list[TemplateResponse]:
        """Return all templates saved by the user."""
        templates = await self._repo.list_user_templates(user_id)
        return [_template_to_response(t) for t in templates]

    async def get_user_template(self, template_id: UUID, user_id: UUID) -> TemplateResponse:
        """Fetch a specific user template."""
        template = await self._repo.get_user_template(template_id, user_id)
        if template is None:
            raise NotFoundError("Template not found")
        return _template_to_response(template)

    async def delete_user_template(self, template_id: UUID, user_id: UUID) -> None:
        """Delete a user template."""
        deleted = await self._repo.delete_user_template(template_id, user_id)
        if not deleted:
            raise NotFoundError("Template not found")

    # ── Resume Parsing ───────────────────────────────────────────────────

    async def parse_resume(self, user_id: UUID, resume_id: UUID) -> ParseResumeResponse:
        """Extract skills, experience, and technologies from a resume.

        Uses keyword-based pattern matching on the resume filename and
        metadata.  Full document parsing requires the file bytes (Sprint 5+).
        """
        resume = await self._repo.get_resume_with_content(resume_id, user_id)
        if resume is None:
            raise NotFoundError("Resume not found")

        filename = resume.original_filename.lower()
        extracted_skills, extracted_techs = _extract_technologies(filename)
        content = resume.parsed_content or ""

        suggested_lang = _suggest_language(filename + " " + content)

        return ParseResumeResponse(
            id=resume.id,
            original_filename=resume.original_filename,
            skills=[ParsedSkill(name=s, category="technical", confidence=0.7) for s in extracted_skills],
            experience=[],
            technologies=extracted_techs,
            suggested_language=suggested_lang,
            suggested_role=None,
            years_of_experience=0,
        )

    # ── Job Description Analysis ──────────────────────────────────────────

    async def analyze_job_description(self, user_id: UUID, jd_id: UUID) -> AnalyzeJdResponse:
        """Analyze a job description to extract skills, technologies, and requirements.

        Performs keyword-based extraction on ``raw_content``.  Full semantic
        analysis requires the AI engine (Sprint 5+).
        """
        jd = await self._repo.get_job_description_with_content(jd_id, user_id)
        if jd is None:
            raise NotFoundError("Job description not found")

        content = (jd.raw_content or "") + " " + (jd.parsed_content or "")
        extracted_skills, extracted_techs = _extract_technologies(content)
        suggested_lang = _suggest_language(content)
        focus_areas = _suggest_focus_areas(content)

        return AnalyzeJdResponse(
            id=jd.id,
            source=jd.source,
            skills=[ParsedSkill(name=s, category="technical", confidence=0.6) for s in extracted_skills],
            technologies=extracted_techs,
            requirements=[],
            suggested_language=suggested_lang,
            suggested_focus_areas=focus_areas,
        )

    # ── Difficulty Estimate ──────────────────────────────────────────────

    async def estimate_difficulty(
        self,
        company: str,
        role: str,
        experience_level: str,
        language: str | None = None,
    ) -> DifficultyEstimateResponse:
        """Return a rule-based difficulty estimate for a configuration.

        Companies known for harder interviews (Google, Meta, Netflix, etc.)
        add to the difficulty score.  Senior roles and higher experience
        levels also increase the estimate.
        """
        score = 3.0  # baseline "medium"
        factors: list[dict[str, str]] = []

        company_lower = company.lower().strip()
        if company_lower in _HARD_COMPANIES:
            score += 1.5
            factors.append({"factor": "company", "detail": f"{company} is known for difficult interviews"})
        elif company_lower in _MEDIUM_COMPANIES:
            score += 0.5
            factors.append({"factor": "company", "detail": f"{company} has moderately difficult interviews"})

        senior_roles = {
            "senior",
            "staff",
            "principal",
            "lead",
            "manager",
            "architect",
        }
        if any(w in role.lower() for w in senior_roles):
            score += 1.0
            factors.append({"factor": "role", "detail": f"Senior-level roles ({role}) are more demanding"})

        if experience_level == "staff-lead":
            score += 0.5
            factors.append({"factor": "seniority", "detail": "Staff/Lead positions require broader knowledge"})
        elif experience_level == "junior":
            score -= 0.5
            factors.append({"factor": "seniority", "detail": "Junior positions focus on fundamentals"})

        if language:
            if language in {"cpp", "java"}:
                score += 0.3
                factors.append(
                    {"factor": "language", "detail": f"{language} interviews often involve deeper systems knowledge"}
                )

        score = max(1.0, min(5.0, score))

        if score >= 4.5:
            overall = "very_hard"
            desc = (
                "This combination is considered very challenging. "
                "Expect advanced system design and deep algorithmic questions."
            )
        elif score >= 3.5:
            overall = "hard"
            desc = (
                "This configuration is on the harder side. "
                "Prepare for complex problem-solving and in-depth discussions."
            )
        elif score >= 2.5:
            overall = "medium"
            desc = "Standard interview difficulty. A balanced mix of fundamentals and applied knowledge."
        else:
            overall = "easy"
            desc = "Entry-level difficulty. Focus on core concepts and common patterns."

        return DifficultyEstimateResponse(
            overall=overall,
            score=round(score, 1),
            factors=factors,
            description=desc,
        )

    # ── Config Validation ────────────────────────────────────────────────

    async def validate_config(
        self,
        interview_type: str,
        company: str,
        role: str,
        experience_level: str,
        language: str | None = None,
        duration_minutes: int = 30,
    ) -> ValidateConfigResponse:
        """Check an interview configuration for completeness and consistency.

        Returns a score (0–100) and a list of warnings.
        """
        warnings: list[ConfigValidationWarning] = []
        deductions = 0

        if interview_type == "coding" and not language:
            warnings.append(
                ConfigValidationWarning(
                    field="language",
                    message="Programming language is required for coding interviews",
                    severity="error",
                )
            )
            deductions += 25

        if not company:
            warnings.append(
                ConfigValidationWarning(
                    field="company",
                    message="Company is required",
                    severity="error",
                )
            )
            deductions += 25

        if not role:
            warnings.append(
                ConfigValidationWarning(
                    field="role",
                    message="Role is required",
                    severity="error",
                )
            )
            deductions += 20

        if not experience_level:
            warnings.append(
                ConfigValidationWarning(
                    field="experience_level",
                    message="Experience level is required",
                    severity="error",
                )
            )
            deductions += 20

        if duration_minutes < 15:
            warnings.append(
                ConfigValidationWarning(
                    field="duration_minutes",
                    message="Duration should be at least 15 minutes",
                    severity="warning",
                )
            )
            deductions += 5

        if experience_level == "junior" and company.lower().strip() in _HARD_COMPANIES:
            warnings.append(
                ConfigValidationWarning(
                    field="experience_level",
                    message=f"Junior level at {company} is uncommon — consider mid-senior or expect a harder interview",
                    severity="info",
                )
            )
            deductions += 5

        score = max(0, 100 - deductions)

        return ValidateConfigResponse(
            score=score,
            warnings=warnings,
            is_ready=score >= 50,
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
        spoken_language=interview.spoken_language,
        framework=interview.framework,
        difficulty=interview.difficulty,
        duration_minutes=interview.duration_minutes,
        custom_instructions=interview.custom_instructions,
        system_design_problem=interview.system_design_problem,
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
    "Databricks",
    "Riot Games",
    "ByteDance",
    "TikTok",
    "Snap",
    "Pinterest",
    "Reddit",
]

# ── Template helper ──────────────────────────────────────────────────────────


def _template_to_response(template) -> TemplateResponse:
    return TemplateResponse(
        id=template.id,
        name=template.name,
        description=template.description,
        interview_type=template.interview_type,
        company=template.company,
        role=template.role,
        experience_level=template.experience_level,
        language=template.language,
        framework=template.framework,
        difficulty=template.difficulty,
        duration_minutes=template.duration_minutes,
        custom_instructions=template.custom_instructions,
        system_design_problem=template.system_design_problem,
        resume_id=template.resume_id,
        job_description_id=template.job_description_id,
        created_at=template.created_at,
    )


# ── Parsing / Analysis helpers ───────────────────────────────────────────────


TECH_KEYWORDS: dict[str, list[str]] = {
    "python": ["python", "django", "flask", "fastapi", "pytorch", "tensorflow", "numpy", "pandas"],
    "javascript": ["javascript", "js", "node", "express", "react", "vue", "angular", "typescript", "ts"],
    "java": ["java", "spring", "hibernate", "maven", "gradle", "kotlin"],
    "cpp": ["c++", "cpp", "cplusplus", "rust", "systems programming"],
    "csharp": ["c#", "csharp", "dotnet", ".net", "asp.net", "azure"],
}

ALL_TECH_KEYWORDS: set[str] = set()
for keywords in TECH_KEYWORDS.values():
    ALL_TECH_KEYWORDS.update(keywords)

FOCUS_AREA_KEYWORDS: dict[str, list[str]] = {
    "system_design": ["system design", "architecture", "distributed", "scalability", "microservices"],
    "algorithms": ["algorithm", "data structure", "leetcode", "complexity", "sorting", "searching"],
    "machine_learning": ["machine learning", "ml", "deep learning", "nlp", "computer vision", "ai"],
    "database": ["sql", "nosql", "database", "postgres", "mysql", "mongodb", "redis"],
    "cloud": ["aws", "gcp", "azure", "cloud", "kubernetes", "docker", "devops", "ci/cd"],
    "frontend": ["react", "vue", "angular", "css", "html", "frontend", "ui", "ux"],
    "backend": ["backend", "api", "rest", "graphql", "server", "middleware"],
}


def _extract_technologies(text: str) -> tuple[list[str], list[str]]:
    """Extract skill and technology names from text using keyword matching."""
    text_lower = text.lower()
    found_skills: list[str] = []
    found_techs: list[str] = []

    for lang, keywords in TECH_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                found_skills.append(lang)
                found_techs.append(kw)

    # Deduplicate while preserving order
    seen_skills: set[str] = set()
    unique_skills: list[str] = []
    for s in found_skills:
        if s not in seen_skills:
            seen_skills.add(s)
            unique_skills.append(s)

    seen_techs: set[str] = set()
    unique_techs: list[str] = []
    for t in found_techs:
        if t not in seen_techs:
            seen_techs.add(t)
            unique_techs.append(t)

    return unique_skills, unique_techs


def _suggest_language(text: str) -> str | None:
    """Suggest a programming language based on keyword frequency in text."""
    text_lower = text.lower()
    scores: dict[str, int] = {}
    for lang, keywords in TECH_KEYWORDS.items():
        scores[lang] = sum(1 for kw in keywords if kw in text_lower)
    best = max(scores, key=scores.get) if scores else None
    return best if best and scores[best] > 0 else None


def _suggest_focus_areas(text: str) -> list[str]:
    """Suggest interview focus areas based on keyword matching."""
    text_lower = text.lower()
    areas: list[str] = []
    for area, keywords in FOCUS_AREA_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            areas.append(area)
    return areas


# ── Company difficulty tiers ─────────────────────────────────────────────────


_HARD_COMPANIES: set[str] = {
    "google",
    "meta",
    "netflix",
    "palantir",
    "databricks",
    "stripe",
    "riot games",
    "snowflake",
    "two sigma",
    "jane street",
    "citadel",
}

_MEDIUM_COMPANIES: set[str] = {
    "amazon",
    "apple",
    "microsoft",
    "uber",
    "airbnb",
    "linkedin",
    "twitter",
    "slack",
    "square",
    "pinterest",
    "reddit",
    "nvidia",
    "adobe",
    "salesforce",
    "oracle",
    "ibm",
    "intel",
}

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
