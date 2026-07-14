"""Pydantic schemas for the interview feature.

Request models validate incoming JSON; response models serialise data
returned to the client.  All models follow the project convention of
``{"success": True, "data": <model>}`` via ``success_response()``.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

# ── Constants ──────────────────────────────────────────────────────────────

InterviewType = Literal["coding", "system-design", "behavioral"]
ExperienceLevel = Literal["junior", "mid-senior", "staff-lead"]
ProgrammingLanguage = Literal["python", "java", "cpp", "javascript", "csharp"]
Difficulty = Literal["easy", "medium", "hard"]
Framework = Literal["react", "vue", "angular", "svelte", "django", "fastapi", "spring", "express", "next"]
DurationMinutes = Literal[15, 30, 45]

ALLOWED_MIME_RESUME = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
ALLOWED_MIME_JD = {
    "application/pdf",
    "text/plain",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5 MB


# ── Request Models ──────────────────────────────────────────────────────────


class CreateInterviewRequest(BaseModel):
    """POST /interviews body."""

    type: InterviewType
    company: str = Field(min_length=1, max_length=100)
    role: str = Field(min_length=1, max_length=100)
    experience_level: ExperienceLevel
    language: ProgrammingLanguage | None = None
    framework: Framework | None = None
    difficulty: Difficulty = "medium"
    duration_minutes: DurationMinutes = 30
    custom_instructions: str | None = Field(None, max_length=2000)
    resume_id: UUID | None = None
    job_description_id: UUID | None = None
    template_id: UUID | None = None
    device_checks: dict[str, bool] = Field(default_factory=dict)

    @model_validator(mode="after")
    def require_language_for_coding(self) -> CreateInterviewRequest:
        if self.type == "coding" and not self.language:
            raise ValueError("language is required for coding interviews")
        return self


class UploadResumeRequest(BaseModel):
    """POST /interviews/upload-resume body (metadata only; file sent as multipart)."""

    original_filename: str = Field(min_length=1, max_length=255)
    mime_type: str
    file_size: int = Field(ge=1, le=MAX_UPLOAD_SIZE)
    file_hash: str = Field(min_length=32, max_length=64)

    @field_validator("mime_type")
    @classmethod
    def validate_mime_type(cls, v: str) -> str:
        if v not in ALLOWED_MIME_RESUME:
            raise ValueError(f"Unsupported file type: {v}. Allowed: PDF, DOCX.")
        return v


class UploadJobDescriptionRequest(BaseModel):
    """POST /interviews/upload-job-description body.

    Accepts either raw text or an uploaded file (hash reference).
    """

    source: Literal["text", "file"] = "text"
    raw_text: str | None = Field(None, max_length=10000)
    original_filename: str | None = Field(None, max_length=255)
    mime_type: str | None = None
    file_size: int | None = Field(None, ge=1, le=MAX_UPLOAD_SIZE)
    file_hash: str | None = Field(None, min_length=32, max_length=64)

    @model_validator(mode="after")
    def validate_source(self) -> UploadJobDescriptionRequest:
        if self.source == "text" and not self.raw_text:
            raise ValueError("raw_text is required when source is 'text'")
        if self.source == "file" and not self.file_hash:
            raise ValueError("file_hash is required when source is 'file'")
        return self


class DeviceCheckRequest(BaseModel):
    """POST /interviews/device-check body."""

    microphone: bool = False
    camera: bool = False
    speaker: bool = False
    browser: bool = False


# ── Response Models ─────────────────────────────────────────────────────────


class InterviewResponse(BaseModel):
    """Full interview representation returned after creation or fetch."""

    id: UUID
    type: str
    company: str
    role: str
    experience_level: str
    language: str | None = None
    framework: str | None = None
    difficulty: str = "medium"
    duration_minutes: int = 30
    custom_instructions: str | None = None
    status: str = "pending"
    timer_remaining: int = 1800
    resume_id: UUID | None = None
    job_description_id: UUID | None = None
    template_id: UUID | None = None
    created_at: datetime


class ResumeResponse(BaseModel):
    """Resume upload confirmation."""

    id: UUID
    original_filename: str
    mime_type: str
    file_size: int
    file_hash: str
    created_at: datetime


class JobDescriptionResponse(BaseModel):
    """Job description upload confirmation."""

    id: UUID
    source: str
    original_filename: str
    created_at: datetime


class DeviceCheckResponse(BaseModel):
    """Device check result."""

    microphone: bool
    camera: bool
    speaker: bool
    browser: bool
    all_passed: bool


# ── Options Response ────────────────────────────────────────────────────────


class InterviewOptionsResponse(BaseModel):
    """GET /interviews/options — all selectable options for the setup wizard."""

    interview_types: list[dict[str, str]]
    companies: list[str]
    roles: list[str]
    languages: list[dict[str, str]]
    frameworks: list[dict[str, str]]
    experience_levels: list[dict[str, str]]
    difficulties: list[dict[str, str]]
    durations: list[dict[str, str]]


# ── Template Schemas ─────────────────────────────────────────────────────────


class CreateTemplateRequest(BaseModel):
    """POST /interviews/templates body."""

    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    interview_type: InterviewType
    company: str = Field(min_length=1, max_length=100)
    role: str = Field(min_length=1, max_length=100)
    experience_level: ExperienceLevel
    language: ProgrammingLanguage | None = None
    framework: Framework | None = None
    difficulty: Difficulty = "medium"
    duration_minutes: DurationMinutes = 30
    custom_instructions: str | None = Field(None, max_length=2000)
    resume_id: UUID | None = None
    job_description_id: UUID | None = None


class TemplateResponse(BaseModel):
    """User template representation."""

    id: UUID
    name: str
    description: str | None = None
    interview_type: str
    company: str
    role: str
    experience_level: str
    language: str | None = None
    framework: str | None = None
    difficulty: str = "medium"
    duration_minutes: int = 30
    custom_instructions: str | None = None
    resume_id: UUID | None = None
    job_description_id: UUID | None = None
    created_at: datetime


# ── Resume Parsing ───────────────────────────────────────────────────────────


class ParsedSkill(BaseModel):
    """A single skill extracted from a resume or job description."""

    name: str
    category: str = "general"
    confidence: float = 0.0


class ParsedExperience(BaseModel):
    """An experience entry extracted from a resume."""

    title: str
    company: str = ""
    duration_years: int = 0
    technologies: list[str] = []


class ParseResumeResponse(BaseModel):
    """Result of resume parsing."""

    id: UUID
    original_filename: str
    skills: list[ParsedSkill]
    experience: list[ParsedExperience]
    technologies: list[str]
    suggested_language: str | None = None
    suggested_role: str | None = None
    years_of_experience: int = 0


# ── Job Description Analysis ─────────────────────────────────────────────────


class JdRequirement(BaseModel):
    """A requirement extracted from a job description."""

    text: str
    category: str = "general"
    importance: str = "required"


class AnalyzeJdResponse(BaseModel):
    """Result of job description analysis."""

    id: UUID
    source: str
    skills: list[ParsedSkill]
    technologies: list[str]
    requirements: list[JdRequirement]
    suggested_language: str | None = None
    suggested_focus_areas: list[str] = []


# ── Difficulty Estimate ──────────────────────────────────────────────────────


class DifficultyEstimateResponse(BaseModel):
    """Estimated interview difficulty for a given configuration."""

    overall: str
    score: float
    factors: list[dict[str, str]]
    description: str


# ── Configuration Validation ─────────────────────────────────────────────────


class ConfigValidationWarning(BaseModel):
    """A warning about the interview configuration."""

    field: str
    message: str
    severity: str = "warning"


class ValidateConfigResponse(BaseModel):
    """Result of configuration validation."""

    score: float
    warnings: list[ConfigValidationWarning]
    is_ready: bool
