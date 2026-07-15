"""Failure scenario tests for the code execution system."""

from __future__ import annotations

import pytest

from judge.judge import judge_output
from judge.sandbox import Sandbox


@pytest.mark.asyncio
class TestFailureScenarios:
    async def test_empty_source_code(self):
        result = await Sandbox.run(
            source_code="",
            language="python",
            test_input="",
            file_extension=".py",
            run_command="python3 /code/solution.py",
        )
        assert result.exit_code == 0

    async def test_only_comments(self):
        result = await Sandbox.run(
            source_code="# just a comment\n# another comment",
            language="python",
            test_input="",
            file_extension=".py",
            run_command="python3 /code/solution.py",
        )
        assert result.exit_code == 0

    async def test_unicode_output(self):
        code = 'print("Hello, 世界! 🌍")'
        result = await Sandbox.run(
            source_code=code,
            language="python",
            test_input="",
            file_extension=".py",
            run_command="python3 /code/solution.py",
        )
        assert "世界" in result.stdout
        assert "🌍" in result.stdout

    async def test_large_memory_allocation(self):
        code = "try:\n    x = [0] * 100_000_000\n    print(len(x))\nexcept MemoryError:\n    print('oom')"
        result = await Sandbox.run(
            source_code=code,
            language="python",
            test_input="",
            time_limit_s=2,
            memory_limit_mb=50,  # Tight limit
            file_extension=".py",
            run_command="python3 /code/solution.py",
        )
        # Should either hit the memory limit or handle it gracefully
        assert result.exit_code in (0, -9)

    async def test_judge_floating_point(self):
        assert judge_output("0.3", "0.3", tolerance=1e-9) is True
        assert judge_output("3.14159", "3.141592", tolerance=1e-4) is True
        assert judge_output("3.14", "3.15", tolerance=1e-3) is False

    async def test_judge_newline_sensitivity(self):
        assert judge_output("line1\nline2\n", "line1\nline2") is True

    async def test_multiline_output(self):
        code = "for i in range(3):\n    print(i)"
        result = await Sandbox.run(
            source_code=code,
            language="python",
            test_input="",
            file_extension=".py",
            run_command="python3 /code/solution.py",
        )
        lines = result.stdout.strip().split("\n")
        assert len(lines) == 3
        assert lines == ["0", "1", "2"]
