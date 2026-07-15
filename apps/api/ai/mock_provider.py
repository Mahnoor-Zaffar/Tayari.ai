"""Mock AI provider for development without an API key.

Returns canned responses so the interview flow can be tested
without calling any external AI service.
"""

from __future__ import annotations

from ai.provider import AIProvider, AIResponse


MOCK_QUESTIONS = [
    "Welcome! Let's start with an easy one. Can you describe your approach to designing a scalable web application?",
    "Interesting. How would you handle a sudden spike in traffic to 10x your normal load?",
    "Good points. Can you tell me about a time you had to debug a complex production issue?",
    "Thanks. How do you approach testing for a new feature you're building?",
    "Let's talk about databases. When would you choose a NoSQL database over a relational one?",
]

MOCK_EVALUATION = {
    "overall_score": 3.8,
    "dimensions": {
        "technical_communication": {"score": 4.0, "evidence": "Clear explanation of system design trade-offs"},
        "problem_solving": {"score": 3.5, "evidence": "Good approach to traffic spike scenario"},
        "code_quality": {"score": 4.0, "evidence": "Well-structured responses"},
        "language_proficiency": {"score": 3.5, "evidence": "Clear technical vocabulary"},
    },
    "hire_verdict": "lean-hire",
    "strengths": ["System design thinking", "Clear communication"],
    "improvements": ["More depth on database choices", "More specific examples"],
    "overall_assessment": "Candidate demonstrated solid engineering fundamentals and good communication skills.",
}


class MockProvider(AIProvider):
    """AI provider that returns canned responses for development."""

    def __init__(self) -> None:
        self._question_index = 0

    async def chat(
        self,
        messages: list[dict],
        system_prompt: str | None = None,
        max_tokens: int = 1000,
    ) -> AIResponse:
        idx = self._question_index
        self._question_index += 1
        content = (
            MOCK_QUESTIONS[idx % len(MOCK_QUESTIONS)]
            if idx < len(MOCK_QUESTIONS)
            else "Thank you for your answer. Let me ask you one more thing — how do you stay current with industry trends?"
        )
        return AIResponse(
            content=content,
            model="mock",
            usage={"prompt_tokens": 50, "completion_tokens": 30},
            latency_ms=200,
        )

    async def chat_stream(self, messages: list[dict], system_prompt: str | None = None):
        yield "Mock streaming response"

    async def structured_output(
        self,
        messages: list[dict],
        response_model: type,
        system_prompt: str | None = None,
    ) -> dict:
        return MOCK_EVALUATION
