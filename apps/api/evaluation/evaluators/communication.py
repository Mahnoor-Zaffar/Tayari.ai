"""Communication evaluator — scores clarity, structure, and articulation.

Runs alongside type-specific evaluators for all interview types.
"""

from __future__ import annotations

from typing import Any

from ai.provider import AIProvider
from evaluation.evaluators.base import BaseEvaluator


class CommunicationEvaluator(BaseEvaluator):
    """Evaluates communication skills across all interview types."""

    PROMPT = (
        "You are an expert communication evaluator. Rate the candidate's communication "
        "during this interview segment.\n\n"
        "## Transcript\n{transcript}\n\n"
        "## Evaluation Dimensions\n"
        "- clarity (weight 30%): Were answers clear and easy to follow?\n"
        "- structure (weight 30%): Were answers well-organized?\n"
        "- conciseness (weight 20%): Were answers appropriately detailed without rambling?\n"
        "- confidence (weight 20%): Did the candidate sound confident?\n\n"
        'Return JSON: {{"overall_score": <0.0-5.0>, '
        '"dimensions": {{"clarity": {{"score": <0.0-5.0>, "evidence": "..."}}, '
        '"structure": {{"score": <0.0-5.0>, "evidence": "..."}}, '
        '"conciseness": {{"score": <0.0-5.0>, "evidence": "..."}}, '
        '"confidence": {{"score": <0.0-5.0>, "evidence": "..."}}}}, '
        '"confidence": <0.0-1.0>}}'
    )

    def __init__(self, provider: AIProvider) -> None:
        super().__init__(provider)

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
        prompt = self.PROMPT.format(transcript=transcript or "No transcript.")
        try:
            response = await self._provider.structured_output(
                messages=[{"role": "user", "content": "Evaluate communication."}],
                response_model=dict,
                system_prompt=prompt,
            )
            return response if isinstance(response, dict) else {}
        except Exception:
            return {}
