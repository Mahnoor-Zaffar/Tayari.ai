"""Recommendation Service — generates learning recommendations from evaluation results.

Produces actionable suggestions for improvement based on dimension scores,
strengths, and weaknesses.
"""

from __future__ import annotations

from evaluation.types import EvaluationResult


class RecommendationService:
    """Generates structured learning recommendations from evaluation results."""

    DIMENSION_RESOURCES: dict[str, list[str]] = {
        "correctness": [
            "Practice with LeetCode Medium/Hard problems",
            "Review edge case handling strategies",
            "Study test-driven development (TDD) patterns",
        ],
        "efficiency": [
            "Study Big O notation and complexity analysis",
            "Practice optimizing brute-force solutions",
            "Review common data structure time complexities",
        ],
        "code_quality": [
            "Read clean code principles (Martin, 2008)",
            "Practice refactoring exercises",
            "Study language-specific best practices",
        ],
        "technical_communication": [
            "Practice explaining solutions out loud",
            "Record yourself solving problems and review",
            "Study the STAR method for technical explanations",
        ],
        "language_proficiency": [
            "Review language-specific documentation",
            "Practice with standard library functions",
            "Complete language-focused coding challenges",
        ],
        "structure_star": [
            "Practice the STAR framework with common questions",
            "Prepare 3-5 stories for each competency",
            "Review behavioral interview guides",
        ],
        "relevance": [
            "Practice active listening in mock interviews",
            "Study the question-answer mapping technique",
            "Get feedback on answer relevance",
        ],
        "specificity": [
            "Prepare concrete metrics for past achievements",
            "Practice quantifying impact in answers",
            "Review the PAR (Problem-Action-Result) framework",
        ],
        "impact": [
            "Track and measure your project outcomes",
            "Practice discussing lessons learned",
            "Study how to frame achievements effectively",
        ],
        "requirements_gathering": [
            "Practice clarifying ambiguous requirements",
            "Study system design interview frameworks",
            "Review functional vs non-functional requirements",
        ],
        "architecture": [
            "Study distributed systems fundamentals",
            "Practice designing systems at different scales",
            "Review common architecture patterns",
        ],
        "trade_off_analysis": [
            "Practice comparing alternative architectures",
            "Study CAP theorem and consistency models",
            "Review real-world architecture case studies",
        ],
        "communication": [
            "Practice structured explanations",
            "Study whiteboard communication techniques",
            "Get feedback on presentation clarity",
        ],
    }

    def generate(self, result: EvaluationResult) -> list[str]:
        """Generate recommendations based on evaluation results."""
        recommendations: list[str] = []
        seen: set[str] = set()

        for dim in result.dimensions:
            if dim.score < 3.0 and dim.key in self.DIMENSION_RESOURCES:
                for rec in self.DIMENSION_RESOURCES[dim.key]:
                    if rec not in seen:
                        recommendations.append(rec)
                        seen.add(rec)

        # Add general recommendations if specific ones are thin
        if len(recommendations) < 2:
            recommendations.append("Continue practicing with mock interviews")
            recommendations.append("Review fundamentals in your weaker areas")

        return recommendations[:5]  # Max 5 recommendations
