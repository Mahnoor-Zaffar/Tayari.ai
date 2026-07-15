"""Core types for the AI Evaluation Engine.

All structured outputs from the AI provider must pass through
these schemas for validation before persisting to the database.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DimensionScore:
    """A single scored dimension with supporting evidence."""

    key: str
    label: str
    score: float  # 0.0 – 5.0
    weight: float = 1.0
    evidence: str = ""
    confidence: float = 1.0  # 0.0 – 1.0


@dataclass
class EvaluationResult:
    """Validated, normalized output ready for persistence.

    This is the **only** object that should be written to the DB.
    AI raw output must pass through ``ResultValidator`` first.
    """

    interview_id: str
    interview_type: str
    overall_score: float  # 0.0 – 5.0
    overall_score_100: float  # 0 – 100
    hire_verdict: str
    dimensions: list[DimensionScore]
    strengths: list[str]
    improvements: list[str]
    recommendations: list[str]
    confidence: float  # 0.0 – 1.0
    raw_evaluation: str = ""
    model_used: str = ""
    prompt_version: str = ""
    evaluated_by: str = "gpt-4o"


INTERVIEW_TYPE_DIMENSIONS: dict[str, list[dict]] = {
    "coding": [
        {"key": "correctness", "label": "Correctness", "weight": 0.30},
        {"key": "efficiency", "label": "Efficiency", "weight": 0.20},
        {"key": "code_quality", "label": "Code Quality", "weight": 0.20},
        {"key": "technical_communication", "label": "Technical Communication", "weight": 0.15},
        {"key": "language_proficiency", "label": "Language Proficiency", "weight": 0.15},
    ],
    "system-design": [
        {"key": "requirements_gathering", "label": "Requirements Gathering", "weight": 0.20},
        {"key": "architecture", "label": "Architecture", "weight": 0.30},
        {"key": "trade_off_analysis", "label": "Trade-off Analysis", "weight": 0.30},
        {"key": "communication", "label": "Communication", "weight": 0.20},
    ],
    "behavioral": [
        {"key": "structure_star", "label": "Structure (STAR)", "weight": 0.30},
        {"key": "relevance", "label": "Relevance", "weight": 0.25},
        {"key": "specificity", "label": "Specificity", "weight": 0.25},
        {"key": "impact", "label": "Impact", "weight": 0.20},
    ],
}


def get_dimensions_for_type(interview_type: str) -> list[dict]:
    """Return the dimension config for a given interview type."""
    return INTERVIEW_TYPE_DIMENSIONS.get(interview_type, INTERVIEW_TYPE_DIMENSIONS["behavioral"])


def compute_hire_verdict(score: float) -> str:
    if score >= 4.0:
        return "hire"
    if score >= 3.0:
        return "lean_hire"
    if score >= 2.0:
        return "lean_no_hire"
    return "no_hire"
