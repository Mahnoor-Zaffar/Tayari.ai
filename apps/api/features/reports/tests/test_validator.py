"""Tests for the evaluation result validator."""

from __future__ import annotations

import pytest

from evaluation.types import EvaluationResult
from evaluation.validator import ResultValidator, ValidationError


class TestResultValidator:
    def setup_method(self) -> None:
        self.validator = ResultValidator()

    def test_valid_coding_output(self):
        raw = """
        {
            "overall_score": 4.2,
            "dimensions": {
                "correctness": {"score": 4.5, "evidence": "Passed all test cases"},
                "efficiency": {"score": 4.0, "evidence": "O(n) time, O(1) space"},
                "code_quality": {"score": 4.0, "evidence": "Clean, well-structured"},
                "technical_communication": {"score": 4.0, "evidence": "Clear explanation"},
                "language_proficiency": {"score": 4.5, "evidence": "Good use of Python"}
            },
            "strengths": ["Clear thinking", "Good edge case handling"],
            "improvements": ["Could optimize space"],
            "recommendations": ["Practice more DP problems"],
            "confidence": 0.9
        }
        """
        result = self.validator.validate(raw, "test-id", "coding")
        assert isinstance(result, EvaluationResult)
        # Weighted: (4.5*.30 + 4.0*.20 + 4.0*.20 + 4.0*.15 + 4.5*.15) / 1.0 ≈ 4.23
        assert result.overall_score == pytest.approx(4.22, abs=0.01)
        assert result.hire_verdict == "hire"
        assert len(result.dimensions) == 5
        assert result.confidence == 0.9

    def test_valid_behavioral_output(self):
        raw = """
        {
            "overall_score": 3.5,
            "dimensions": {
                "structure_star": {"score": 4.0, "evidence": "Used STAR framework"},
                "relevance": {"score": 3.5, "evidence": "Addressed the question"},
                "specificity": {"score": 3.0, "evidence": "Could be more specific"},
                "impact": {"score": 3.5, "evidence": "Showed measurable results"}
            },
            "strengths": ["Good structure"],
            "improvements": ["More concrete metrics"],
            "recommendations": ["Practice quantifying impact"],
            "confidence": 0.8
        }
        """
        result = self.validator.validate(raw, "test-id", "behavioral")
        assert result.hire_verdict == "lean-hire"
        assert len(result.dimensions) == 4

    def test_missing_overall_score_raises(self):
        raw = '{"dimensions": {}}'
        with pytest.raises(ValidationError, match="overall_score"):
            self.validator.validate(raw, "test-id", "behavioral")

    def test_score_clamped_to_range(self):
        raw = """
        {
            "overall_score": 10.0,
            "dimensions": {
                "structure_star": {"score": 6.0, "evidence": ""},
                "relevance": {"score": 4.0, "evidence": ""},
                "specificity": {"score": 3.0, "evidence": ""},
                "impact": {"score": 3.0, "evidence": ""}
            },
            "strengths": [], "improvements": [], "recommendations": [],
            "confidence": 1.0
        }
        """
        result = self.validator.validate(raw, "test-id", "behavioral")
        # Clamped: structure_star=5.0 (clamped from 6.0), weighted = (5*.30 + 4*.25 + 3*.25 + 3*.20) / 1.0 = 3.85
        assert result.overall_score == 3.85
        assert all(d.score <= 5.0 for d in result.dimensions)

    def test_markdown_fences_stripped(self):
        raw = (
            '```json\n{"overall_score": 3.0, "dimensions": {}, '
            '"strengths": [], "improvements": [], '
            '"recommendations": [], "confidence": 0.5}\n```'
        )
        result = self.validator.validate(raw, "test-id", "behavioral")
        assert result.overall_score == 3.0

    def test_weighted_scoring(self):
        raw = """
        {
            "overall_score": 3.0,
            "dimensions": {
                "correctness": {"score": 5.0, "evidence": "All tests pass"},
                "efficiency": {"score": 5.0, "evidence": "Optimal"},
                "code_quality": {"score": 5.0, "evidence": "Clean"},
                "technical_communication": {"score": 1.0, "evidence": "Poor"},
                "language_proficiency": {"score": 1.0, "evidence": "Poor"}
            },
            "strengths": [], "improvements": [], "recommendations": [], "confidence": 0.5
        }
        """
        result = self.validator.validate(raw, "test-id", "coding")
        # correctness 0.30 + efficiency 0.20 + code_quality 0.20 + tech_comm 0.15 + lang 0.15
        # = (5*0.30 + 5*0.20 + 5*0.20 + 1*0.15 + 1*0.15) / 1.0 = 3.8
        assert result.overall_score == 3.8
