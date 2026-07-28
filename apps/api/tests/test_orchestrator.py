"""Tests for the AI orchestrator — turn loop, question limits, wrap-up."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.provider import AIResponse
from ai.realtime.memory_manager import ConversationMemory
from ai.realtime.orchestrator import AIOrchestrator
from ai.realtime.prompt_builder import PromptBuilder
from ai.realtime.transcript_manager import TranscriptManager


@pytest.fixture
def mock_provider():
    provider = MagicMock()
    provider.chat = AsyncMock(
        return_value=AIResponse(
            content="What is your approach to designing a scalable system?",
            model="gpt-4o-mini",
            usage={"total_tokens": 50},
            latency_ms=200,
        )
    )
    provider.chat_stream = AsyncMock()
    provider.structured_output = AsyncMock(
        return_value={
            "overall_score": 4.0,
            "hire_verdict": "hire",
            "dimensions": {},
            "strengths": [],
            "improvements": [],
        }
    )
    return provider


@pytest.fixture
def orchestrator(mock_provider):
    return AIOrchestrator(
        provider=mock_provider,
        prompt_builder=PromptBuilder(),
        memory=ConversationMemory(system_prompt="You are an interviewer."),
        transcript=TranscriptManager(),
        interview_type="behavioral",
        duration_minutes=30,
    )


class TestGenerateInitialQuestion:
    @pytest.mark.asyncio
    async def test_returns_question_text(self, orchestrator):
        question = await orchestrator.generate_initial_question()
        assert isinstance(question, str)
        assert len(question) > 0

    @pytest.mark.asyncio
    async def test_appends_to_memory(self, orchestrator):
        await orchestrator.generate_initial_question()
        messages = orchestrator._memory.get_all_messages()
        assert len(messages) == 2  # system + assistant
        assert messages[-1]["role"] == "assistant"

    @pytest.mark.asyncio
    async def test_appends_to_transcript(self, orchestrator):
        await orchestrator.generate_initial_question()
        transcript = orchestrator._transcript.get_transcript()
        assert len(transcript) >= 1


class TestProcessAnswer:
    @pytest.mark.asyncio
    async def test_returns_next_question(self, orchestrator):
        await orchestrator.generate_initial_question()
        next_q = await orchestrator.process_answer("I would start by understanding the requirements.")
        assert next_q is not None
        assert isinstance(next_q, str)

    @pytest.mark.asyncio
    async def test_appends_answer_to_memory(self, orchestrator):
        await orchestrator.generate_initial_question()
        await orchestrator.process_answer("My approach is to use microservices.")
        messages = orchestrator._memory.get_all_messages()
        user_msgs = [m for m in messages if m["role"] == "user"]
        assert len(user_msgs) == 1
        assert "microservices" in user_msgs[0]["content"]

    @pytest.mark.asyncio
    async def test_returns_none_at_question_limit(self, orchestrator):
        orchestrator._max_questions = lambda: 1  # type: ignore[method-assign]
        await orchestrator.generate_initial_question()
        result = await orchestrator.process_answer("My answer.")
        assert result is None


class TestQuestionLimit:
    def test_behavioral_max_questions(self):
        assert (
            AIOrchestrator(
                provider=MagicMock(),
                prompt_builder=MagicMock(),
                memory=MagicMock(),
                transcript=MagicMock(),
                interview_type="behavioral",
                duration_minutes=30,
            )._max_questions()
            == 15
        )  # max(12, 30//2)

    def test_coding_max_questions(self):
        assert (
            AIOrchestrator(
                provider=MagicMock(),
                prompt_builder=MagicMock(),
                memory=MagicMock(),
                transcript=MagicMock(),
                interview_type="coding",
                duration_minutes=30,
            )._max_questions()
            == 6
        )  # max(6, 30//5)

    def test_shorter_interview_fewer_questions(self):
        assert (
            AIOrchestrator(
                provider=MagicMock(),
                prompt_builder=MagicMock(),
                memory=MagicMock(),
                transcript=MagicMock(),
                interview_type="coding",
                duration_minutes=15,
            )._max_questions()
            == 6
        )  # max(6, 15//5)


class TestWrapUp:
    @pytest.mark.asyncio
    async def test_generates_wrap_up_message(self, orchestrator):
        msg = await orchestrator.generate_wrap_up()
        assert "That's all the time we have" in msg

    @pytest.mark.asyncio
    async def test_appends_to_memory(self, orchestrator):
        await orchestrator.generate_wrap_up()
        messages = orchestrator._memory.get_all_messages()
        assert "That's all the time we have" in messages[-1]["content"]


class TestHint:
    @pytest.mark.asyncio
    async def test_returns_hint(self, mock_provider):
        mock_provider.chat = AsyncMock(
            return_value=AIResponse(
                content="Try using a hash map for O(1) lookups.",
                model="gpt-4o-mini",
                usage={"total_tokens": 30},
                latency_ms=100,
            )
        )
        orch = AIOrchestrator(
            provider=mock_provider,
            prompt_builder=MagicMock(),
            memory=ConversationMemory(system_prompt="test"),
            transcript=TranscriptManager(),
        )
        hint = await orch.generate_hint()
        assert hint is not None
        assert "hash map" in hint


class TestEvaluate:
    @pytest.mark.asyncio
    async def test_returns_evaluation(self, mock_provider, orchestrator):
        result = await orchestrator.evaluate(
            interview_type="coding",
            company="TestCo",
            role="Engineer",
            experience_level="mid-senior",
        )
        assert result["overall_score"] == 4.0
        assert result["hire_verdict"] == "hire"
