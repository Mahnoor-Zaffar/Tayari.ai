"""Tests for the recommendation service."""

from __future__ import annotations

from evaluation.recommendations import RecommendationService
from evaluation.types import DimensionScore, EvaluationResult


class TestRecommendationService:
    def setup_method(self) -> None:
        self.service = RecommendationService()

    def test_recommendations_for_low_scores(self):
        result = EvaluationResult(
            interview_id="test",
            interview_type="coding",
            overall_score=2.5,
            overall_score_100=50.0,
            hire_verdict="lean-no-hire",
            dimensions=[
                DimensionScore(key="correctness", label="Correctness", score=2.0, weight=0.3),
                DimensionScore(key="efficiency", label="Efficiency", score=3.0, weight=0.2),
            ],
            strengths=[],
            improvements=[],
            recommendations=[],
            confidence=0.8,
        )
        recs = self.service.generate(result)
        assert len(recs) > 0
        assert any("LeetCode" in r for r in recs)

    def test_recommendations_for_high_scores(self):
        result = EvaluationResult(
            interview_id="test",
            interview_type="behavioral",
            overall_score=4.5,
            overall_score_100=90.0,
            hire_verdict="hire",
            dimensions=[
                DimensionScore(key="structure_star", label="STAR", score=5.0, weight=0.3),
                DimensionScore(key="relevance", label="Relevance", score=5.0, weight=0.25),
            ],
            strengths=[],
            improvements=[],
            recommendations=[],
            confidence=0.9,
        )
        recs = self.service.generate(result)
        assert len(recs) <= 5
