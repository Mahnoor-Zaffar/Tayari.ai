"""Base evaluator interface — all interview type evaluators inherit from this."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ai.provider import AIProvider


class BaseEvaluator(ABC):
    """Evaluates a specific interview type.

    Each evaluator:
    1. Builds a type-specific prompt from transcript + metadata
    2. Calls the AI provider
    3. Validates structured output
    4. Returns partial scores (to be aggregated later)
    """

    def __init__(self, provider: AIProvider) -> None:
        self._provider = provider

    @abstractmethod
    async def evaluate(
        self,
        interview_id: str,
        company: str,
        role: str,
        experience_level: str,
        transcript: str,
        language: str = "",
        code_submission: str = "",
        test_results: str = "",
    ) -> dict[str, Any]:
        """Evaluate the interview and return raw dimension scores.

        Returns a dict with:
        - overall_score: float
        - dimensions: {key: {score, evidence}}
        - strengths: list[str]
        - improvements: list[str]
        - confidence: float
        """
        ...
