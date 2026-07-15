"""Result Validator — parses, validates, and normalizes AI evaluation output.

The LLM must **never** write directly to the database.
All AI output must pass through this validator first.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from evaluation.types import DimensionScore, EvaluationResult, compute_hire_verdict, get_dimensions_for_type

logger = logging.getLogger(__name__)

MAX_RETRIES = 2


class ValidationError(Exception):
    pass


class ResultValidator:
    """Validates raw AI evaluation output and produces a normalized EvaluationResult.

    Pipeline:
        1. Parse JSON from AI response
        2. Check required fields exist
        3. Validate score ranges (0.0 – 5.0)
        4. Extract dimension scores with evidence
        5. Compute weighted overall score
        6. Produce clean EvaluationResult for persistence
    """

    def validate(
        self,
        raw_json: str,
        interview_id: str,
        interview_type: str,
        model_used: str = "",
        prompt_version: str = "",
    ) -> EvaluationResult:
        """Parse and validate raw AI output.

        Raises ValidationError if the output cannot be parsed or
        is structurally invalid.
        """
        parsed = self._parse_json(raw_json)
        self._validate_structure(parsed, interview_type)

        dims_config = get_dimensions_for_type(interview_type)
        dim_config_map = {d["key"]: d for d in dims_config}

        dimensions: list[DimensionScore] = []
        ai_dims = parsed.get("dimensions", {})

        for dim_config in dims_config:
            key = dim_config["key"]
            ai_dim = ai_dims.get(key, {})

            score = float(ai_dim.get("score", 0))
            score = max(0.0, min(5.0, score))

            dimensions.append(DimensionScore(
                key=key,
                label=dim_config["label"],
                score=score,
                weight=dim_config["weight"],
                evidence=str(ai_dim.get("evidence", "")),
                confidence=float(ai_dim.get("confidence", 0.8)),
            ))

        ai_overall = float(parsed.get("overall_score", 0))
        ai_overall = max(0.0, min(5.0, ai_overall))

        weighted = self._compute_weighted(dimensions)

        overall = weighted if weighted > 0 else ai_overall

        confidence = float(parsed.get("confidence", 0.8))
        confidence = max(0.0, min(1.0, confidence))

        return EvaluationResult(
            interview_id=interview_id,
            interview_type=interview_type,
            overall_score=round(overall, 2),
            overall_score_100=round(overall / 5.0 * 100, 1),
            hire_verdict=compute_hire_verdict(overall),
            dimensions=dimensions,
            strengths=[str(s) for s in parsed.get("strengths", [])],
            improvements=[str(s) for s in parsed.get("improvements", [])],
            recommendations=[str(s) for s in parsed.get("recommendations", [])],
            confidence=round(confidence, 2),
            raw_evaluation=raw_json,
            model_used=model_used,
            prompt_version=prompt_version,
        )

    def _parse_json(self, raw: str) -> dict[str, Any]:
        """Parse JSON from AI response, stripping markdown fences if present."""
        text = raw.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1])

        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValidationError(f"Failed to parse AI output as JSON: {exc}") from exc

    def _validate_structure(self, parsed: dict[str, Any], interview_type: str) -> None:
        """Validate that required fields exist in the parsed output."""
        if "overall_score" not in parsed:
            raise ValidationError("Missing required field: overall_score")

        dims = parsed.get("dimensions", {})
        expected = {d["key"] for d in get_dimensions_for_type(interview_type)}

        missing = expected - set(dims.keys())
        if missing:
            logger.warning("Missing dimensions in AI output: %s", missing)

    def _compute_weighted(self, dimensions: list[DimensionScore]) -> float:
        total_weight = sum(d.weight for d in dimensions)
        if total_weight == 0:
            return 0.0
        return sum(d.score * d.weight for d in dimensions) / total_weight
