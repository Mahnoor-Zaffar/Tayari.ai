"""Coding interview evaluator."""

from __future__ import annotations

from typing import Any

from ai.provider import AIProvider
from evaluation.evaluators.base import BaseEvaluator
from evaluation.prompt_registry import PromptRegistry


class CodingEvaluator(BaseEvaluator):
    """Evaluates coding interviews — correctness, efficiency, code quality, communication, language."""

    PROMPT_TYPE = "coding"

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
            transcript=transcript, language=language,
            code_submission=code_submission, test_results=test_results,
        )
        return await self._call_ai(prompt)

    async def _call_ai(self, prompt: str) -> dict[str, Any]:
        try:
            response = await self._provider.structured_output(
                messages=[{"role": "user", "content": "Evaluate this coding interview."}],
                response_model=dict,
                system_prompt=prompt,
            )
            if isinstance(response, dict):
                return response
            import json
            return json.loads(response) if isinstance(response, str) else {}
        except Exception:
            return {}
