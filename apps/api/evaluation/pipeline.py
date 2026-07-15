"""Evaluation Pipeline — orchestrates the full evaluation flow.

1. Collect transcript + metadata + code results
2. Build evaluation prompt
3. Call AI provider
4. Validate response
5. Calculate scores
6. Persist evaluation
7. Return result
"""

from __future__ import annotations

import logging
from typing import Any

from ai.provider import AIProvider
from ai.openai_provider import OpenAIProvider
from evaluation.code_analysis import CodeAnalysisService
from evaluation.prompt_registry import PromptRegistry
from evaluation.scoring import ScoringEngine
from evaluation.transcript_analyzer import TranscriptAnalyzer
from evaluation.types import EvaluationResult
from evaluation.validator import ResultValidator, ValidationError

logger = logging.getLogger(__name__)

MAX_RETRIES = 2


class EvaluationPipeline:
    """End-to-end evaluation pipeline for all interview types.

    The LLM **never** writes to the database.  All output passes
    through ``ResultValidator`` which produces a clean ``EvaluationResult``.
    """

    def __init__(
        self,
        provider: AIProvider | None = None,
    ) -> None:
        self._provider = provider or OpenAIProvider()
        self._prompt_registry = PromptRegistry()
        self._transcript_analyzer = TranscriptAnalyzer()
        self._code_analysis = CodeAnalysisService()
        self._validator = ResultValidator()
        self._scoring = ScoringEngine()

    async def evaluate(
        self,
        interview_id: str,
        interview_type: str,
        company: str,
        role: str,
        experience_level: str,
        transcript: list[dict],
        language: str = "",
        code_submission: dict[str, Any] | None = None,
        model: str = "gpt-4o",
        prompt_version: str = "v1",
    ) -> EvaluationResult:
        """Run the full evaluation pipeline for an interview.

        Returns a validated, normalized ``EvaluationResult`` ready
        for persistence.
        """
        formatted_transcript = self._transcript_analyzer.format_for_prompt(transcript)
        code_text = self._code_analysis.code_for_prompt(code_submission)
        test_results_text = self._code_analysis._format_test_results(
            (code_submission or {}).get("test_results", [])
        )

        eval_prompt = self._prompt_registry.build_prompt(
            interview_type=interview_type,
            company=company,
            role=role,
            experience_level=experience_level,
            transcript=formatted_transcript,
            language=language,
            code_submission=code_text,
            test_results=test_results_text,
            version=prompt_version,
        )

        last_error: Exception | None = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                response = await self._provider.structured_output(
                    messages=[{"role": "user", "content": "Evaluate this interview."}],
                    response_model=dict,
                    system_prompt=eval_prompt,
                )

                raw_json = response if isinstance(response, str) else str(response)
                # Some providers return dict directly
                if isinstance(response, dict):
                    raw_json = str(response)
                    # Wrap in ValidationResult for consistent handling
                    result = self._validator.validate(
                        raw_json=raw_json,
                        interview_id=interview_id,
                        interview_type=interview_type,
                        model_used=model,
                        prompt_version=prompt_version,
                    )
                    # Overwrite raw_evaluation with actual dict
                    import json
                    result.raw_evaluation = json.dumps(response)
                    return result

                result = self._validator.validate(
                    raw_json=raw_json,
                    interview_id=interview_id,
                    interview_type=interview_type,
                    model_used=model,
                    prompt_version=prompt_version,
                )
                return result

            except ValidationError as exc:
                last_error = exc
                logger.warning("Validation attempt %d/%d failed: %s", attempt + 1, MAX_RETRIES + 1, exc)
                if attempt < MAX_RETRIES:
                    continue
                break

            except Exception as exc:
                last_error = exc
                logger.error("AI call attempt %d/%d failed: %s", attempt + 1, MAX_RETRIES + 1, exc)
                if attempt < MAX_RETRIES:
                    continue
                break

        # All retries exhausted — return fallback evaluation
        logger.error("Evaluation failed for interview %s after %d attempts", interview_id[:8], MAX_RETRIES + 1)
        return EvaluationResult(
            interview_id=interview_id,
            interview_type=interview_type,
            overall_score=0.0,
            overall_score_100=0.0,
            hire_verdict="error",
            dimensions=[],
            strengths=[],
            improvements=[],
            recommendations=[],
            confidence=0.0,
            raw_evaluation=str(last_error) if last_error else "Evaluation failed",
            model_used=model,
            prompt_version=prompt_version,
        )
