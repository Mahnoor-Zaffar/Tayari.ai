"""Tests for the test case judge."""

from __future__ import annotations

from judge.judge import is_numeric_output, judge_output, judge_test_cases, normalize_output


class TestNormalizeOutput:
    def test_strips_trailing_whitespace(self):
        assert normalize_output("hello  \n") == "hello"

    def test_normalizes_newlines(self):
        assert normalize_output("a\r\nb") == "a\nb"

    def test_empty_string(self):
        assert normalize_output("") == ""


class TestIsNumericOutput:
    def test_integer(self):
        assert is_numeric_output("42") is True

    def test_float(self):
        assert is_numeric_output("3.14") is True

    def test_negative(self):
        assert is_numeric_output("-42") is True

    def test_text_is_not_numeric(self):
        assert is_numeric_output("hello") is False

    def test_multiline_is_not_numeric(self):
        assert is_numeric_output("1\n2") is False


class TestJudgeOutput:
    def test_exact_match(self):
        assert judge_output("hello", "hello") is True

    def test_ignores_trailing_whitespace(self):
        assert judge_output("hello  \n", "hello") is True

    def test_numeric_tolerance(self):
        assert judge_output("3.14159", "3.141592", tolerance=1e-4) is True

    def test_numeric_outside_tolerance(self):
        assert judge_output("3.14", "3.15", tolerance=1e-3) is False

    def test_different_strings(self):
        assert judge_output("abc", "xyz") is False


class TestJudgeTestCases:
    def test_all_pass(self):
        cases = [
            {"id": "1", "input": "2\n3", "expected_output": "5", "is_hidden": False},
            {"id": "2", "input": "10\n20", "expected_output": "30", "is_hidden": True},
        ]
        outputs = {"1": "5", "2": "30"}
        result = judge_test_cases(cases, outputs)
        assert result["overall_passed"] == 2
        assert result["overall_total"] == 2
        assert result["visible_passed"] == 1
        assert result["hidden_passed"] == 1

    def test_hidden_output_not_exposed(self):
        cases = [
            {"id": "1", "input": "x", "expected_output": "y", "is_hidden": True},
        ]
        outputs = {"1": "wrong"}
        result = judge_test_cases(cases, outputs)
        assert result["results"][0]["actual_output"] is None
        assert result["results"][0]["passed"] is False

    def test_visible_output_exposed(self):
        cases = [
            {"id": "1", "input": "x", "expected_output": "y", "is_hidden": False},
        ]
        outputs = {"1": "right"}
        result = judge_test_cases(cases, outputs)
        assert result["results"][0]["actual_output"] == "right"

    def test_some_fail(self):
        cases = [
            {"id": "1", "input": "", "expected_output": "a", "is_hidden": False},
            {"id": "2", "input": "", "expected_output": "b", "is_hidden": False},
            {"id": "3", "input": "", "expected_output": "c", "is_hidden": True},
        ]
        outputs = {"1": "a", "2": "wrong", "3": "c"}
        result = judge_test_cases(cases, outputs)
        assert result["overall_passed"] == 2
        assert result["overall_total"] == 3
