"""AI orchestration service.

Manages the turn-based interview loop:
  1. Load prompt → 2. Generate AI question → 3. Stream to client
  4. Wait for user answer → 5. Append to memory → 6. Repeat
  7. On completion → wrap-up → trigger evaluation
"""

from __future__ import annotations

import logging
import time

from ai.provider import AIProvider
from ai.realtime.memory_manager import ConversationMemory
from ai.realtime.prompt_builder import PromptBuilder
from ai.realtime.transcript_manager import TranscriptManager

logger = logging.getLogger(__name__)

WRAP_UP_MESSAGE = (
    "That's all the time we have. Thank you for your responses today. "
    "The interviewer will now step out while the evaluation is prepared."
)


class AIOrchestrator:
    """Manages the AI-driven turn loop for a single interview session."""

    SAFETY_MAX_QUESTIONS = 30

    def __init__(
        self,
        provider: AIProvider,
        prompt_builder: PromptBuilder,
        memory: ConversationMemory,
        transcript: TranscriptManager,
        max_tokens: int = 800,
        interview_type: str = "coding",
        duration_minutes: int = 30,
    ) -> None:
        self._provider = provider
        self._prompt_builder = prompt_builder
        self._memory = memory
        self._transcript = transcript
        self._max_tokens = max_tokens
        self._interview_type = interview_type
        self._duration_minutes = duration_minutes
        self._current_question_id = 0
        self._last_question = ""
        self._question_count = 0
        self._started_at: float | None = None

    def _remaining_time_context(self) -> str:
        """Build a short time-remaining string injected at each turn."""
        if self._started_at is None:
            elapsed = 0
        else:
            elapsed = time.time() - self._started_at
        remaining = max(0, self._duration_minutes * 60 - int(elapsed))
        mins = remaining // 60
        return f"[Time: ~{mins} of {self._duration_minutes} minutes remaining]"

    async def generate_initial_question(self) -> str:
        """Generate the opening question from the AI interviewer."""
        self._started_at = time.time()
        self._current_question_id += 1
        self._question_count += 1
        question = await self._generate_question(is_initial=True)
        self._last_question = question
        self._memory.append("assistant", question)
        self._transcript.append_static("ai", question)
        return question

    async def process_answer(self, answer: str) -> str | None:
        """Process a user answer and generate the next AI response.

        Returns the next question text, or None if the interview
        should proceed to wrap-up (safety ceiling hit).
        """
        self._memory.append("user", answer)
        self._transcript.commit_partial("user")

        if self._question_count >= self.SAFETY_MAX_QUESTIONS:
            logger.warning("Safety question ceiling hit (%s)", self.SAFETY_MAX_QUESTIONS)
            return None

        self._current_question_id += 1
        self._question_count += 1
        next_question = await self._generate_question(is_initial=False)

        if next_question is None:
            return None

        self._last_question = next_question
        self._memory.append("assistant", next_question)
        self._transcript.append_static("ai", next_question)
        return next_question

    async def generate_wrap_up(self) -> str:
        """Generate the concluding remarks from the AI."""
        self._memory.append("assistant", WRAP_UP_MESSAGE)
        self._transcript.append_static("ai", WRAP_UP_MESSAGE)
        return WRAP_UP_MESSAGE

    async def generate_hint(self, question_id: int | None = None) -> str | None:
        """Generate a hint for the current or specified question."""
        messages = self._memory.get_all_messages()
        messages.append(
            {
                "role": "user",
                "content": "Can you give me a hint? I'm stuck.",
            }
        )
        response = await self._provider.chat(
            messages=messages,
            system_prompt="You are a helpful interview coach. Give a brief hint (1-2 sentences) "
            "that guides the candidate without giving away the full solution.",
            max_tokens=150,
        )
        hint = response.content.strip()
        if hint:
            self._transcript.append_static("ai", hint)
        return hint or None

    async def evaluate(
        self,
        interview_type: str,
        company: str,
        role: str,
        experience_level: str,
        language: str | None = None,
    ) -> dict:
        """Run evaluation on the completed transcript (blocking, in worker)."""
        evaluator_prompt = self._prompt_builder.build_evaluator_prompt(
            interview_type=interview_type,
            company=company,
            role=role,
            experience_level=experience_level,
            language=language,
        )
        transcript_text = self._transcript.full_text
        messages = [
            {"role": "user", "content": f"Here is the interview transcript:\n\n{transcript_text}"},
        ]
        result = await self._provider.structured_output(
            messages=messages,
            response_model=dict,
            system_prompt=evaluator_prompt,
        )
        return result

    async def _generate_question(self, is_initial: bool = False) -> str | None:
        """Call the AI provider to generate the next question.

        Returns the question text, or None if the provider fails.
        """
        messages = list(self._memory.get_all_messages())
        messages.append({"role": "system", "content": self._remaining_time_context()})
        try:
            response = await self._provider.chat(
                messages=messages,
                max_tokens=self._max_tokens,
            )
            return response.content.strip()
        except Exception as exc:
            logger.error("AI generation failed: %s", exc)
            return None

    @property
    def last_question(self) -> str:
        return self._last_question
