"""Score Aggregator — combines partial scores from multiple evaluators into a final score.

Each evaluator returns dimension scores independently. The aggregator:
1. Collects all dimensions from all evaluators
2. Applies weights per dimension
3. Computes weighted overall score
4. Merges strengths and improvements
5. Computes aggregate confidence
"""

from __future__ import annotations

from evaluation.types import DimensionScore


class ScoreAggregator:
    """Combines partial scores from multiple evaluators."""

    def aggregate(
        self,
        evaluator_results: list[dict],
    ) -> tuple[list[DimensionScore], float, float, list[str], list[str]]:
        """Aggregate dimension scores from all evaluator results.

        Returns:
            (dimensions, overall_score, confidence, strengths, improvements)
        """
        all_dims: dict[str, DimensionScore] = {}
        all_strengths: list[str] = []
        all_improvements: list[str] = []
        confidences: list[float] = []

        for result in evaluator_results:
            ai_dims = result.get("dimensions", {})
            for key, data in ai_dims.items():
                if key not in all_dims:
                    score = float(data.get("score", 0))
                    weight = float(data.get("weight", 1.0))
                    all_dims[key] = DimensionScore(
                        key=key,
                        label=key.replace("_", " ").title(),
                        score=max(0.0, min(5.0, score)),
                        weight=weight,
                        evidence=str(data.get("evidence", "")),
                        confidence=float(data.get("confidence", 0.8)),
                    )

            all_strengths.extend(result.get("strengths", []))
            all_improvements.extend(result.get("improvements", []))
            confidences.append(float(result.get("confidence", 0.8)))

        dimensions = list(all_dims.values())
        overall = self._compute_weighted(dimensions)
        avg_confidence = sum(confidences) / max(len(confidences), 1)

        return (
            dimensions,
            round(overall, 2),
            round(avg_confidence, 2),
            all_strengths[:5],
            all_improvements[:5],
        )

    def _compute_weighted(self, dimensions: list[DimensionScore]) -> float:
        total_weight = sum(d.weight for d in dimensions)
        if total_weight == 0:
            return 0.0
        return sum(d.score * d.weight for d in dimensions) / total_weight
