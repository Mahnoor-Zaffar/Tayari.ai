"""Tests for the scoring engine."""

from __future__ import annotations

from evaluation.scoring import ScoringEngine
from evaluation.types import DimensionScore


class TestScoringEngine:
    def setup_method(self) -> None:
        self.engine = ScoringEngine()

    def test_compute_overall(self):
        dims = [
            DimensionScore(key="a", label="A", score=5.0, weight=0.5),
            DimensionScore(key="b", label="B", score=3.0, weight=0.5),
        ]
        overall = self.engine.compute_overall(dims)
        assert overall == 4.0

    def test_all_perfect_scores(self):
        dims = [DimensionScore(key="x", label="X", score=5.0, weight=1.0) for _ in range(3)]
        assert self.engine.compute_overall(dims) == 5.0

    def test_all_zero_scores(self):
        dims = [DimensionScore(key="x", label="X", score=0.0, weight=1.0) for _ in range(3)]
        assert self.engine.compute_overall(dims) == 0.0

    def test_normalize_to_100(self):
        assert self.engine.normalize_to_100(4.0) == 80.0
        assert self.engine.normalize_to_100(5.0) == 100.0
        assert self.engine.normalize_to_100(0.0) == 0.0

    def test_compute_confidence(self):
        dims = [
            DimensionScore(key="a", label="A", score=4.0, confidence=0.9),
            DimensionScore(key="b", label="B", score=3.0, confidence=0.7),
        ]
        confidence = self.engine.compute_confidence(dims)
        assert confidence == 0.8

    def test_get_max_dimension(self):
        dims = [
            DimensionScore(key="low", label="Low", score=2.0),
            DimensionScore(key="high", label="High", score=5.0),
        ]
        assert self.engine.get_max_dimension(dims).key == "high"
        assert self.engine.get_min_dimension(dims).key == "low"
