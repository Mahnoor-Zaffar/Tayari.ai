"""Tests for the code execution service and API routes."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from features.code.repository import CodeRepository
from features.code.seed_data import SEED_PROBLEMS
from features.code.service import CodeExecutionService
from judge.queue import ExecutionQueue


@pytest.fixture
def mock_repo():
    repo = MagicMock(spec=CodeRepository)
    repo.create_submission = AsyncMock()
    repo.create_submission.return_value = MagicMock(id="mock-submission-id")
    repo.get_submission = AsyncMock()
    repo.update_submission = AsyncMock()
    repo.get_problem = AsyncMock()
    return repo


@pytest.fixture
def service(mock_repo):
    return CodeExecutionService(repo=mock_repo, queue=ExecutionQueue(max_concurrent=1))


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
            source_code="print(int(input()) + int(input()))",
            test_inputs=["2\n3", "10\n20", "100\n200"],
        )
        assert result["status"] == "completed"
        assert result["total_count"] == 3

    async def test_submit_unknown_problem_raises(self, service: CodeExecutionService, mock_repo):
        mock_repo.get_problem.return_value = None
        with pytest.raises(ValueError, match="Unknown problem"):
            await service.submit_code(
                interview_id="00000000-0000-0000-0000-000000000001",
                user_id="00000000-0000-0000-0000-000000000002",
                language="python",
                source_code="print(1)",
                problem_id="00000000-0000-0000-0000-000000000009",
            )

    async def test_submit_with_problem_runs_hidden_tests(self, service: CodeExecutionService, mock_repo):
        two_sum = next(p for p in SEED_PROBLEMS if p["slug"] == "two-sum")
        mock_repo.get_problem.return_value = MagicMock(id="p1", test_cases=two_sum["test_cases"])

        source = (
            "import sys\n"
            "def solve(data):\n"
            "    parts = data.split()\n"
            "    n = int(parts[0])\n"
            "    nums = list(map(int, parts[1:1+n]))\n"
            "    target = int(parts[1+n])\n"
            "    seen = {}\n"
            "    for i, x in enumerate(nums):\n"
            "        if target - x in seen:\n"
            "            return f'{seen[target-x]} {i}'\n"
            "        seen[x] = i\n"
            "    return ''\n"
            "if __name__ == '__main__':\n"
            "    print(solve(sys.stdin.read()))\n"
        )
        result = await service.submit_code(
            interview_id="00000000-0000-0000-0000-000000000001",
            user_id="00000000-0000-0000-0000-000000000002",
            language="python",
            source_code=source,
            problem_id="p1",
        )
        assert result["status"] == "completed"
        assert result["total_count"] == len(two_sum["test_cases"])
        assert result["passed_count"] == len(two_sum["test_cases"])
        hidden = [r for r in result["test_results"] if r["is_hidden"]]
        assert len(hidden) > 0
        for r in hidden:
            assert r["passed"] is True
            assert r["actual_output"] is None

    async def test_submit_with_problem_failing_hidden_test(self, service: CodeExecutionService, mock_repo):
        reverse_string = next(p for p in SEED_PROBLEMS if p["slug"] == "reverse-string")
        mock_repo.get_problem.return_value = MagicMock(id="p2", test_cases=reverse_string["test_cases"])

        # Only handles a single token; the multi-word hidden case fails.
        source = (
            "import sys\n"
            "def solve(data):\n"
            "    return data.strip()\n"
            "if __name__ == '__main__':\n"
            "    print(solve(sys.stdin.read()))\n"
        )
        result = await service.submit_code(
            interview_id="00000000-0000-0000-0000-000000000001",
            user_id="00000000-0000-0000-0000-000000000002",
            language="python",
            source_code=source,
            problem_id="p2",
        )
        assert result["total_count"] == len(reverse_string["test_cases"])
        assert result["passed_count"] < result["total_count"]
        failed = [r for r in result["test_results"] if not r["passed"]]
        assert any(r["is_hidden"] for r in failed)
        assert all(r["actual_output"] is None for r in result["test_results"] if r["is_hidden"])
