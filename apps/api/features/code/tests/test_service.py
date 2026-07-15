"""Tests for the code execution service and API routes."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from features.code.repository import CodeRepository
from features.code.service import CodeExecutionService


@pytest.fixture
def mock_repo():
    repo = MagicMock(spec=CodeRepository)
    repo.create_submission = AsyncMock()
    repo.create_submission.return_value = MagicMock(id="mock-submission-id")
    repo.get_submission = AsyncMock()
    repo.update_submission = AsyncMock()
    return repo


@pytest.fixture
def service(mock_repo):
    return CodeExecutionService(mock_repo)


@pytest.mark.asyncio
class TestCodeExecutionService:
    async def test_run_code_unknown_language(self, service: CodeExecutionService):
        with pytest.raises(ValueError, match="Unsupported language"):
            await service.run_code("brainfuck", "code")

    async def test_submit_code_unknown_language(self, service: CodeExecutionService):
        with pytest.raises(ValueError, match="Unsupported language"):
            await service.submit_code(
                interview_id="00000000-0000-0000-0000-000000000001",
                user_id="00000000-0000-0000-0000-000000000001",
                language="brainfuck",
                source_code="code",
            )

    async def test_get_languages_returns_all(self, service: CodeExecutionService):
        langs = service.get_languages()
        lang_ids = {lang["id"] for lang in langs}
        assert "python" in lang_ids
        assert "java" in lang_ids
        assert "cpp" in lang_ids

    async def test_run_code_python_hello(self, service: CodeExecutionService):
        result = await service.run_code("python", 'print("ok")')
        assert result.exit_code == 0
        assert "ok" in result.stdout

    async def test_submit_with_test_inputs(self, service: CodeExecutionService):
        result = await service.submit_code(
            interview_id="00000000-0000-0000-0000-000000000001",
            user_id="00000000-0000-0000-0000-000000000002",
            language="python",
            source_code='print(int(input()) + int(input()))',
            test_inputs=["2\n3", "10\n20", "100\n200"],
        )
        assert result["status"] == "completed"
        assert result["total_count"] == 3
