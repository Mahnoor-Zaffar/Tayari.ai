"""Tests for the code execution judge — pure logic, no sandbox needed."""

from judge.judge import judge_output, judge_test_cases, normalize_output


class TestNormalizeOutput:
    def test_strips_trailing_whitespace(self):
        assert normalize_output("hello  \n") == "hello"

    def test_normalizes_newlines(self):
        assert normalize_output("a\r\nb\r\nc") == "a\nb\nc"

    def test_preserves_internal_spaces(self):
        assert normalize_output("  hello world  ") == "  hello world"


class TestJudgeOutput:
    def test_exact_match(self):
        assert judge_output("hello", "hello")

    def test_match_after_normalization(self):
        assert judge_output("hello\n", "hello")

    def test_numeric_match(self):
        assert judge_output("42", "42.0")

    def test_numeric_tolerance(self):
        assert judge_output("3.14159", "3.14160", tolerance=1e-4)
        assert not judge_output("3.14159", "3.14200", tolerance=1e-4)

    def test_non_numeric_not_fooled(self):
        assert not judge_output("hello", "42")

    def test_empty_strings(self):
        assert judge_output("", "")


class TestJudgeTestCases:
    def test_all_pass(self):
        result = judge_test_cases(
            test_cases=[
                {"id": "t1", "expected_output": "hello", "is_hidden": False},
                {"id": "t2", "expected_output": "42", "is_hidden": False},
            ],
            actual_outputs={"t1": "hello\n", "t2": "42.0"},
        )
        assert result["overall_passed"] == 2
        assert result["overall_total"] == 2

    def test_hidden_cases_not_leaked(self):
        result = judge_test_cases(
            test_cases=[
                {"id": "t1", "expected_output": "secret", "is_hidden": True},
            ],
            actual_outputs={"t1": "wrong"},
        )
        assert result["results"][0]["actual_output"] is None
        assert result["results"][0]["passed"] is False

    def test_mixed_results(self):
        result = judge_test_cases(
            test_cases=[
                {"id": "t1", "expected_output": "a", "is_hidden": False},
                {"id": "t2", "expected_output": "b", "is_hidden": False},
                {"id": "t3", "expected_output": "c", "is_hidden": True},
            ],
            actual_outputs={"t1": "a", "t2": "wrong", "t3": "c"},
        )
        assert result["visible_passed"] == 1
        assert result["visible_total"] == 2
        assert result["hidden_passed"] == 1
        assert result["overall_passed"] == 2
