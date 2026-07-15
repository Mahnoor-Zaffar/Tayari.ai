"""Evaluation Pipeline — orchestrates the modular evaluation flow.

Interview Complete
        │
        ▼
Transcript Analyzer
        │
        ├── Primary Evaluator (type-specific: coding/behavioral/system-design)
        ├── Cross-cutting Evaluator (communication)
        │
        ▼
Score Aggregator
        │
        ▼
Recommendation Generator
        │
        ▼
Report Composer
        │
        ▼
Structured Validation
        │
        ▼
Persist Evaluation

Each evaluator runs independently.  Scores are combined by the aggregator.
The LLM never writes to the database.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from ai.openai_provider import OpenAIProvider
from evaluation.aggregator import ScoreAggregator
from evaluation.composer import ReportComposer
from evaluation.evaluators import get_evaluators
from evaluation.recommendations import RecommendationService
from evaluation.sanitize import sanitize_source_code, sanitize_transcript
from evaluation.scoring import ScoringEngine
from evaluation.transcript_analyzer import TranscriptAnalyzer
from evaluation.types import EvaluationResult
from evaluation.validator import ResultValidator, ValidationError

logger = logging.getLogger(__name__)

MAX_RETRIES = 2


class EvaluationPipeline:
    """Modular evaluation pipeline with swappable evaluators.

    To add a new evaluator:
    1. Create a class in ``evaluation/evaluators/``
    2. Add it to ``CROSS_CUTTING_EVALUATORS`` or ``PRIMARY_EVALUATORS``
    3. No pipeline code changes needed.
    """

    def __init__(self, provider=None) -> None:
        self._provider = provider or OpenAIProvider()
        self._transcript_analyzer = TranscriptAnalyzer()
        self._aggregator = ScoreAggregator()
        self._composer = ReportComposer()
        self._validator = ResultValidator()
        self._scoring = ScoringEngine()
        self._recommendations = RecommendationService()

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

        1. Analyze transcript
        2. Run all applicable evaluators (primary + cross-cutting)
        3. Aggregate scores
        4. Generate recommendations
        5. Compose report
        6. Validate output
        7. Return normalized EvaluationResult
        """
        raw_text = self._transcript_analyzer.format_for_prompt(transcript)
        safe_transcript = sanitize_transcript(raw_text)

        code_text = ""
        test_results = ""
        from evaluation.code_analysis import CodeAnalysisService
        code_service = CodeAnalysisService()
        if code_submission:
            code_text = sanitize_source_code(
                code_service.code_for_prompt(code_submission)
            )
            test_results = code_service.format_test_results(
                code_submission.get("test_results", [])
            )

        evaluators = get_evaluators(interview_type, self._provider)
        evaluator_results: list[dict] = []
        last_error: Exception | None = None

        for evaluator in evaluators:
            for attempt in range(MAX_RETRIES + 1):
                try:
                    result = await evaluator.evaluate(
                        interview_id=interview_id,
                        company=company,
                        role=role,
                        experience_level=experience_level,
                        transcript=safe_transcript,
                        language=language,
                        code_submission=code_text,
                        test_results=test_results,
                    )
                    if result and "dimensions" in result:
                        evaluator_results.append(result)
                    break
                except Exception as exc:
                    last_error = exc
                    logger.warning(
                        "%s attempt %d/%d failed: %s",
                        type(evaluator).__name__, attempt + 1, MAX_RETRIES + 1, exc,
                    )
                    if attempt >= MAX_RETRIES:
                        logger.error(
                            "%s failed after all retries", type(evaluator).__name__,
                        )

        if not evaluator_results:
            return EvaluationResult(
                interview_id=interview_id,
                interview_type=interview_type,
                overall_score=0.0, overall_score_100=0.0,
                hire_verdict="error",
                dimensions=[], strengths=[], improvements=[], recommendations=[],
                confidence=0.0, status="failed",
                raw_evaluation=str(last_error) if last_error else "All evaluators failed",
                model_used=model, prompt_version=prompt_version,
            )

        dimensions, overall_score, confidence, strengths, improvements = (
            self._aggregator.aggregate(evaluator_results)
        )

        recommendations = self._recommendations.generate_from_dimensions(dimensions)

        result = self._composer.compose(
            interview_id=interview_id,
            interview_type=interview_type,
            dimensions=dimensions,
            overall_score=overall_score,
            confidence=confidence,
            strengths=strengths,
            improvements=improvements,
            recommendations=recommendations,
            raw_evaluation=json.dumps(evaluator_results),
            model_used=model,
            prompt_version=prompt_version,
        )

        try:
            result = self._validator.validate_result(result)
        except ValidationError:
            pass

        return result
