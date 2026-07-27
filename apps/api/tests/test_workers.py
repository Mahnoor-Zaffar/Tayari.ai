"""Tests for the background worker modules — scheduler and evaluation worker."""

import pytest

from workers.evaluation import generate_evaluation


class TestGenerateEvaluation:
    @pytest.mark.asyncio
    async def test_returns_none_on_missing_interview(self):
        result = await generate_evaluation(
            interview_id="00000000-0000-0000-0000-000000000001",
            user_id="00000000-0000-0000-0000-000000000002",
        )
        assert result is None
