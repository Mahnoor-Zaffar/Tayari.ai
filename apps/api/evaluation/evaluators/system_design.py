"""System design interview evaluator."""

from __future__ import annotations

from typing import Any

from ai.provider import AIProvider
from evaluation.evaluators.base import BaseEvaluator
from evaluation.prompt_registry import PromptRegistry


class SystemDesignEvaluator(BaseEvaluator):
    """Evaluates system design interviews — requirements, architecture, trade-offs, communication."""

    PROMPT_TYPE = "system-design"

    def __init__(self, provider: AIProvider) -> None:
        super().__init__(provider)
        self._prompts = PromptRegistry()

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
        prompt = self._prompts.build_prompt(
            interview_type=self.PROMPT_TYPE,
            company=company, role=role, experience_level=experience_level,
            transcript=transcript,
        )
        try:
            response = await self._provider.structured_output(
                messages=[{"role": "user", "content": "Evaluate this system design interview."}],
                response_model=dict,
                system_prompt=prompt,
            )
            return response if isinstance(response, dict) else {}
        except Exception:
            return {}
