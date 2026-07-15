"""Evaluation Pipeline — orchestrates the full evaluation flow.

1. Collect transcript + metadata + code results
2. Sanitize all user-supplied content (PII redaction, prompt injection prevention)
3. Build evaluation prompt
4. Call AI provider with retry logic
5. Validate structured output
6. Calculate scores
7. Return validated EvaluationResult (never raw AI output)

The LLM **never** writes to the database.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from ai.openai_provider import OpenAIProvider
from ai.provider import AIProvider
from evaluation.code_analysis import CodeAnalysisService
from evaluation.prompt_registry import PromptRegistry
from evaluation.sanitize import sanitize_source_code, sanitize_transcript
from evaluation.scoring import ScoringEngine
from evaluation.transcript_analyzer import TranscriptAnalyzer
from evaluation.types import EvaluationResult
from evaluation.validator import ResultValidator, ValidationError

logger = logging.getLogger(__name__)

MAX_RETRIES = 2


class EvaluationPipeline:
    """End-to-end evaluation pipeline for all interview types.

    All AI output passes through ``ResultValidator`` which produces
    a clean ``EvaluationResult`` ready for persistence.
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
        """Run the full evaluation pipeline.

        1. Sanitize all user content (PII redaction, injection prevention)
        2. Build type-specific evaluation prompt
        3. Call AI provider (with retry)
        4. Validate structured output
        5. Return normalized EvaluationResult

        Args:
            interview_id: UUID of the interview being evaluated.
            interview_type: One of ``coding``, ``behavioral``, ``system-design``.
            company: Target company name.
            role: Target role.
            experience_level: Seniority level.
            transcript: Raw transcript segments from the interview.
            language: Programming language (for coding interviews).
            code_submission: Optional code submission with test results.
            model: AI model identifier.
            prompt_version: Prompt version string.

        Returns:
            A validated, normalized EvaluationResult.  On failure after all
            retries, returns a fallback result with ``status="failed"``.
        """
        raw_transcript_text = self._transcript_analyzer.format_for_prompt(transcript)
        safe_transcript = sanitize_transcript(raw_transcript_text)

        code_text = ""
        test_results_text = ""
        if code_submission:
            raw_code = self._code_analysis.code_for_prompt(code_submission)
            code_text = sanitize_source_code(raw_code)
            test_results_text = self._code_analysis.format_test_results(
                code_submission.get("test_results", [])
            )

        eval_prompt = self._prompt_registry.build_prompt(
            interview_type=interview_type,
            company=company,
            role=role,
            experience_level=experience_level,
            transcript=safe_transcript,
            language=language,
            code_submission=code_text,
            test_results=test_results_text,
            version=prompt_version,
        )

        last_error: Exception | None = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                raw = await self._provider.structured_output(
                    messages=[{"role": "user", "content": "Evaluate this interview."}],
                    response_model=dict,
                    system_prompt=eval_prompt,
                )

                raw_json: str = ""

                if isinstance(raw, dict):
                    raw_json = json.dumps(raw)
                elif isinstance(raw, str):
                    raw_json = raw
                else:
                    raw_json = str(raw)

                result = self._validator.validate(
                    raw_json=raw_json,
                    interview_id=interview_id,
                    interview_type=interview_type,
                    model_used=model,
                    prompt_version=prompt_version,
                )

                if isinstance(raw, dict):
                    result.raw_evaluation = json.dumps(raw)

                return result

            except ValidationError as exc:
                last_error = exc
                logger.warning(
                    "Validation attempt %d/%d failed: %s",
                    attempt + 1, MAX_RETRIES + 1, exc,
                )
                if attempt >= MAX_RETRIES:
                    break

            except Exception as exc:
                last_error = exc
                logger.error(
                    "AI call attempt %d/%d failed: %s",
                    attempt + 1, MAX_RETRIES + 1, exc,
                )
                if attempt >= MAX_RETRIES:
                    break

        # All retries exhausted — return fallback
        logger.error(
            "Evaluation failed for interview %s after %d attempts",
            interview_id[:8], MAX_RETRIES + 1,
        )
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
            status="failed",
            raw_evaluation=str(last_error) if last_error else "Evaluation failed",
            model_used=model,
            prompt_version=prompt_version,
        )
