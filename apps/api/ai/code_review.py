"""AI code review service — generates evaluations for submitted code.

This module is a plugin that hooks into the submission pipeline
without modifying the execution engine.  It reads completed
submissions and generates AI reviews asynchronously.
"""

from __future__ import annotations

import logging
from typing import Any

from ai.provider import AIProvider, OpenAIProvider

logger = logging.getLogger(__name__)

CODE_REVIEW_PROMPT = """You are an expert code reviewer. Review the following code submission.

## Submission Context
- Language: {language}
- Problem: {problem_statement}

## Code to Review
```{language}
{source_code}
```

## Test Results
{test_results}

## Evaluation Criteria
1. **Correctness** — Does the code solve the problem? Did all tests pass?
2. **Efficiency** — Is the time/space complexity optimal?
3. **Code Quality** — Is the code readable, well-structured, idiomatic?
4. **Edge Cases** — Are edge cases handled?

## Output Format
Return valid JSON only:
{{
    "overall_score": <0.0-5.0>,
    "dimensions": {{
        "correctness": {{"score": <0.0-5.0>, "evidence": "<specific observation>"}},
        "efficiency": {{"score": <0.0-5.0>, "evidence": "<specific observation>"}},
        "code_quality": {{"score": <0.0-5.0>, "evidence": "<specific observation>"}},
        "edge_cases": {{"score": <0.0-5.0>, "evidence": "<specific observation>"}}
    }},
    "strengths": ["<strength 1>", "<strength 2>"],
    "improvements": ["<improvement 1>", "<improvement 2>"],
    "optimization_suggestions": ["<suggestion 1>", "<suggestion 2>"],
    "complexity_analysis": "O(...) time, O(...) space",
    "overall_assessment": "<2-3 sentence summary>"
}}
"""


class CodeReviewService:
    """Generates AI-powered code reviews for submissions.

    Designed as a plugin — called after execution completes.
    The execution engine is never modified.
    """

    def __init__(self, provider: AIProvider | None = None) -> None:
        self._provider = provider or OpenAIProvider()

    async def generate_review(
        self,
        source_code: str,
        language: str,
        problem_statement: str = "",
        test_results: list[dict] | None = None,
    ) -> dict[str, Any]:
        """Generate a code review for a completed submission.

        Args:
            source_code: The submitted source code.
            language: Programming language identifier.
            problem_statement: The problem description (optional).
            test_results: Test case results from the judge.

        Returns:
            Dict with overall_score, dimensions, strengths, improvements.
        """
        test_summary = self._format_test_results(test_results or [])

        prompt = CODE_REVIEW_PROMPT.format(
            language=language,
            problem_statement=problem_statement or "Unknown",
            source_code=source_code,
            test_results=test_summary,
        )

        try:
            result = await self._provider.structured_output(
                messages=[{"role": "user", "content": "Review this code submission."}],
                response_model=dict,
                system_prompt=prompt,
            )
            return result
        except Exception as exc:
            logger.error("Code review generation failed: %s", exc)
            return {
                "overall_score": None,
                "dimensions": {},
                "strengths": [],
                "improvements": [],
                "optimization_suggestions": [],
                "complexity_analysis": "",
                "overall_assessment": "AI review unavailable.",
            }

    @staticmethod
    def _format_test_results(results: list[dict]) -> str:
        if not results:
            return "No test results available."
        passed = sum(1 for r in results if r.get("passed"))
        total = len(results)
        details = "\n".join(
            f"  Test {i+1}: {'PASS' if r.get('passed') else 'FAIL'}"
            for i, r in enumerate(results)
        )
        return f"{passed}/{total} tests passed\n{details}"


# Singleton for use across the application
_code_review_service: CodeReviewService | None = None


def get_code_review_service() -> CodeReviewService:
    global _code_review_service
    if _code_review_service is None:
        _code_review_service = CodeReviewService()
    return _code_review_service
