"""Scoring Engine — applies configurable rubrics to produce final scores.

Normalizes dimension scores using weight configurations and
computes the final overall score and hire verdict.
"""

from __future__ import annotations

from evaluation.types import DimensionScore


class ScoringEngine:
    """Applies rubrics to produce normalized evaluation scores.

    Supports:
    - Weighted dimension scoring
    - Score normalization across interview types
    - Configurable thresholds for hire verdicts
    """

    def compute_overall(self, dimensions: list[DimensionScore]) -> float:
        """Compute weighted overall score from dimension scores."""
        total_weight = sum(d.weight for d in dimensions)
        if total_weight == 0:
            return 0.0
        return round(sum(d.score * d.weight for d in dimensions) / total_weight, 2)

    def normalize_to_100(self, score: float) -> float:
        """Convert 0.0–5.0 scale to 0–100 scale."""
        return round(score / 5.0 * 100, 1)

    def compute_confidence(self, dimensions: list[DimensionScore]) -> float:
        """Compute overall confidence as average of dimension confidences."""
        if not dimensions:
            return 0.0
        return round(sum(d.confidence for d in dimensions) / len(dimensions), 2)

    def get_max_dimension(self, dimensions: list[DimensionScore]) -> DimensionScore | None:
        return max(dimensions, key=lambda d: d.score) if dimensions else None

    def get_min_dimension(self, dimensions: list[DimensionScore]) -> DimensionScore | None:
        return min(dimensions, key=lambda d: d.score) if dimensions else None
