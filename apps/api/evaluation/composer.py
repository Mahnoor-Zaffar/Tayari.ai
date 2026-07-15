"""Report Composer — builds the final evaluation report from aggregated scores.

Assembles strengths, improvements, recommendations, and metadata
into a complete EvaluationResult ready for validation and persistence.
"""

from __future__ import annotations

from evaluation.types import DimensionScore, EvaluationResult, compute_hire_verdict


class ReportComposer:
    """Builds a complete EvaluationResult from aggregated scores."""

    def compose(
        self,
        interview_id: str,
        interview_type: str,
        dimensions: list[DimensionScore],
        overall_score: float,
        confidence: float,
        strengths: list[str],
        improvements: list[str],
        recommendations: list[str],
        raw_evaluation: str = "",
        model_used: str = "",
        prompt_version: str = "",
    ) -> EvaluationResult:
        """Build a validated, normalized EvaluationResult."""
        return EvaluationResult(
            interview_id=interview_id,
            interview_type=interview_type,
            overall_score=overall_score,
            overall_score_100=round(overall_score / 5.0 * 100, 1),
            hire_verdict=compute_hire_verdict(overall_score),
            dimensions=dimensions,
            strengths=strengths,
            improvements=improvements,
            recommendations=recommendations,
            confidence=confidence,
            status="completed",
            raw_evaluation=raw_evaluation,
            model_used=model_used,
            prompt_version=prompt_version,
        )
