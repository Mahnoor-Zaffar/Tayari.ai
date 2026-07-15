"""Code Analysis Service — analyzes code submissions for evaluation input.

Processes submitted code and test results into structured analysis
that feeds into the evaluation prompt.  Does NOT call the AI provider —
it only prepares data for the evaluation prompt.
"""

from __future__ import annotations

from typing import Any


class CodeAnalysisService:
    """Analyzes code submissions for inclusion in the evaluation prompt.

    Produces:
    - Test result summary (pass/fail counts)
    - Code structure analysis (lines, functions, classes)
    - Compiler output if any
    """

    def analyze_submission(self, submission: dict[str, Any] | None) -> dict[str, Any]:
        if submission is None:
            return {
                "has_submission": False,
                "summary": "No code submitted.",
                "code": "",
                "test_results": "No test results.",
            }

        source = submission.get("source_code", "")
        lines = source.split("\n") if source else []
        test_results = submission.get("test_results", [])
        passed = sum(1 for t in test_results if t.get("passed"))
        total = len(test_results)

        return {
            "has_submission": True,
            "summary": self._summarize_test_results(passed, total),
            "code": source,
            "lines_of_code": len(lines),
            "test_results": self._format_test_results(test_results),
            "compiler_output": submission.get("compiler_output", ""),
            "execution_ms": submission.get("execution_ms"),
        }

    def code_for_prompt(self, submission: dict[str, Any] | None) -> str:
        """Format code analysis as readable text for the evaluation prompt."""
        analysis = self.analyze_submission(submission)
        if not analysis["has_submission"]:
            return "No code submitted."

        parts = [f"```\n{analysis['code']}\n```"]
        parts.append(f"\nTests: {analysis['summary']}")
        if analysis["compiler_output"]:
            parts.append(f"\nCompiler output: {analysis['compiler_output']}")
        if analysis["execution_ms"]:
            parts.append(f"\nExecution time: {analysis['execution_ms']}ms")
        return "\n".join(parts)

    def _summarize_test_results(self, passed: int, total: int) -> str:
        if total == 0:
            return "No tests run."
        return f"{passed}/{total} tests passed."

    def _format_test_results(self, results: list[dict]) -> str:
        if not results:
            return ""
        lines = []
        for i, r in enumerate(results):
            status = "PASS" if r.get("passed") else "FAIL"
            hidden = " (hidden)" if r.get("is_hidden") else ""
            lines.append(f"  Test {i+1}: {status}{hidden}")
        return "\n".join(lines)
