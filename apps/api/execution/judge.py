"""Test case judge — compares actual output to expected output.

Supports exact string matching and floating-point tolerance.
"""

from __future__ import annotations

import re
from typing import Any


def normalize_output(text: str) -> str:
    """Normalize output for comparison: strip trailing space, normalize newlines."""
    return text.rstrip().replace("\r\n", "\n")


def is_numeric_output(text: str) -> bool:
    """Check if output appears to be a number."""
    return bool(re.match(r"^-?\d+(\.\d+)?$", text.strip()))


def judge_output(actual: str, expected: str, tolerance: float = 1e-6) -> bool:
    """Compare actual output to expected output.

    For numeric outputs, uses floating-point tolerance.
    For string outputs, uses exact (normalized) comparison.
    """
    a = normalize_output(actual)
    e = normalize_output(expected)

    if a == e:
        return True

    if is_numeric_output(a) and is_numeric_output(e):
        try:
            return abs(float(a) - float(e)) < tolerance
        except (ValueError, TypeError):
            return False

    return False


def judge_test_cases(
    test_cases: list[dict],
    actual_outputs: dict[str, str],
) -> dict[str, Any]:
    """Run the judge against all test cases.

    Args:
        test_cases: List of dicts with keys: id, input, expected_output, is_hidden
        actual_outputs: Dict mapping test_case_id → actual stdout

    Returns:
        Dict with results, counts, and pass/fail per test.
    """
    results: list[dict] = []
    visible_passed = 0
    visible_total = 0
    hidden_passed = 0
    hidden_total = 0

    for tc in test_cases:
        tc_id = tc["id"]
        actual = actual_outputs.get(tc_id, "")
        expected = tc["expected_output"]
        is_hidden = tc.get("is_hidden", False)

        passed = judge_output(actual, expected)

        results.append({
            "test_case_id": tc_id,
            "passed": passed,
            "is_hidden": is_hidden,
            "actual_output": actual if not is_hidden else None,
        })

        if is_hidden:
            hidden_total += 1
            if passed:
                hidden_passed += 1
        else:
            visible_total += 1
            if passed:
                visible_passed += 1

    return {
        "results": results,
        "visible_passed": visible_passed,
        "visible_total": visible_total,
        "hidden_passed": hidden_passed,
        "hidden_total": hidden_total,
        "overall_passed": visible_passed + hidden_passed,
        "overall_total": visible_total + hidden_total,
    }
