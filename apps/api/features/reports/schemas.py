from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class EvaluationResponse(BaseModel):
    id: UUID
    interview_id: UUID
    overall_score: float | None = None
    dimension_scores: dict = {}
    hire_verdict: str | None = None
    strengths: list = []
    improvements: list = []
    delta_vs_last: float | None = None
    model_used: str | None = None
    status: str
    created_at: datetime
