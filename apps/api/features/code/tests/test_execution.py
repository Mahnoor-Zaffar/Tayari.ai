"""Tests for code execution using subprocess sandbox."""

from __future__ import annotations

import pytest

from judge.sandbox import Sandbox


@pytest.mark.asyncio
class TestCodeExecution:
    async def test_python_hello_world(self):
        result = await Sandbox.run(
            source_code='print("hello")',
            language="python",
            test_input="",
            file_extension=".py",
            run_command="python3 /code/solution.py",
        )
        assert result.stdout.strip() == "hello"
        assert result.exit_code == 0

    async def test_python_with_input(self):
        code = "name = input().strip()\nprint(f'Hello, {name}!')"
        result = await Sandbox.run(
            source_code=code,
            language="python",
            test_input="World",
            file_extension=".py",
            run_command="python3 /code/solution.py",
        )
        assert result.stdout.strip() == "Hello, World!"

    async def test_python_syntax_error(self):
        code = "print(hello"
        result = await Sandbox.run(
            source_code=code,
            language="python",
            test_input="",
            file_extension=".py",
            run_command="python3 /code/solution.py",
        )
        assert result.exit_code != 0
        assert "SyntaxError" in result.stderr or result.exit_code != 0

    async def test_runtime_error(self):
        code = "1 / 0"
        result = await Sandbox.run(
            source_code=code,
            language="python",
            test_input="",
            file_extension=".py",
            run_command="python3 /code/solution.py",
        )
        assert result.exit_code != 0

    async def test_timeout(self):
        code = "while True: pass"
        result = await Sandbox.run(
            source_code=code,
            language="python",
            test_input="",
            time_limit_s=1,
            file_extension=".py",
            run_command="python3 /code/solution.py",
        )
        assert result.timed_out is True

    async def test_infinite_loop_detected(self):
        code = "x = 0\nwhile True:\n    x += 1"
        result = await Sandbox.run(
            source_code=code,
            language="python",
            test_input="",
            time_limit_s=1,
            file_extension=".py",
            run_command="python3 /code/solution.py",
        )
        assert result.timed_out is True

    async def test_large_output_truncated(self):
        code = "print('x' * 200000)"
        result = await Sandbox.run(
            source_code=code,
            language="python",
            test_input="",
            file_extension=".py",
            run_command="python3 /code/solution.py",
        )
        assert len(result.stdout) <= 100_000  # SANDBOX_MAX_OUTPUT_CHARS
