"""Tests for the prompt builder."""

from __future__ import annotations

import pytest

from ai.realtime.prompt_builder import PromptBuilder


@pytest.fixture
def builder() -> PromptBuilder:
    return PromptBuilder()


class TestPromptBuilder:
    def test_load_interviewer_prompt_coding(self, builder: PromptBuilder):
        prompt = builder.build_system_prompt(
            interview_type="coding",
            company="Google",
            role="Software Engineer",
            experience_level="mid-senior",
            language="python",
        )
        assert "Google" in prompt
        assert "coding" in prompt.lower()
        assert "python" in prompt

    def test_load_interviewer_prompt_behavioral(self, builder: PromptBuilder):
        prompt = builder.build_system_prompt(
            interview_type="behavioral",
            company="Meta",
            role="Product Manager",
            experience_level="staff-lead",
        )
        assert "Meta" in prompt

    def test_load_interviewer_prompt_system_design(self, builder: PromptBuilder):
        prompt = builder.build_system_prompt(
            interview_type="system-design",
            company="Amazon",
            role="Senior Engineer",
            experience_level="junior",
        )
        assert "Amazon" in prompt
        assert "system" in prompt.lower()

    def test_custom_instructions_appended(self, builder: PromptBuilder):
        prompt = builder.build_system_prompt(
            interview_type="coding",
            company="Google",
            role="SWE",
            experience_level="mid-senior",
            custom_instructions="Focus on graph algorithms",
        )
        assert "Focus on graph algorithms" in prompt

    def test_invalid_interview_type_raises(self, builder: PromptBuilder):
        with pytest.raises(FileNotFoundError):
            builder.build_system_prompt(
                interview_type="nonexistent",
                company="X",
                role="Y",
                experience_level="junior",
            )

    def test_get_supported_types(self, builder: PromptBuilder):
        types = builder.get_supported_interview_types()
        assert "coding" in types
        assert "behavioral" in types or "Behavioural" in types
        assert "system-design" in types
        assert len(types) >= 3

    def test_evaluator_prompt_coding(self, builder: PromptBuilder):
        prompt = builder.build_evaluator_prompt(
            interview_type="coding",
            company="Google",
            role="SWE",
            experience_level="mid-senior",
            language="python",
        )
        assert "evaluat" in prompt.lower()
