from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class InterviewResponse(BaseModel):
    id: UUID
    type: str
    company: str
    experience_level: str
    language: str | None = None
    status: str
    timer_remaining: int
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None


class CreateInterviewRequest(BaseModel):
    type: str
    company: str
    experience_level: str
    language: str | None = None
