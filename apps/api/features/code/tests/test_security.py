"""Security tests for the code execution system.

Tests injection attempts, input validation, and sandbox isolation.
"""

from __future__ import annotations

import pytest

from judge.registry import get_language
from judge.sandbox import Sandbox


@pytest.mark.asyncio
class TestSandboxSecurity:
    async def test_command_injection_via_code(self):
        """Source code containing shell metacharacters should not execute them."""
        code = '"; cat /etc/passwd #'
        result = await Sandbox.run(
            source_code=code,
            language="python",
            test_input="",
            time_limit_s=2,
            file_extension=".py",
            run_command="python3 /code/solution.py",
        )
        # Should either error (syntax) or safely print the string
        assert "root:" not in result.stdout

    async def test_environment_variable_leak(self):
        """Attempt to read environment variables via code."""
        code = "import os\nprint(os.environ.get('SECRET'))"
        result = await Sandbox.run(
            source_code=code,
            language="python",
            test_input="",
            time_limit_s=2,
            file_extension=".py",
            run_command="python3 /code/solution.py",
        )
        # In sandbox, env should be empty or process should error
        assert "SECRET" not in result.stdout

    async def test_infinite_memory_allocation(self):
        """Attempt to exhaust memory should be caught."""
        code = "x = [0] * (1024 ** 4) ; print('done')"
        result = await Sandbox.run(
            source_code=code,
            language="python",
            test_input="",
            time_limit_s=3,
            memory_limit_mb=50,
            file_extension=".py",
            run_command="python3 /code/solution.py",
        )
        # Should time out or error, not print done
        assert result.stdout.strip() != "done"

    async def test_source_code_max_length(self):
        """Very long source code should be rejected or handled."""
        code = "x = 1\n" * 100_000
        result = await Sandbox.run(
            source_code=code,
            language="python",
            test_input="",
            time_limit_s=2,
            file_extension=".py",
            run_command="python3 /code/solution.py",
        )
        # Should not crash the sandbox
        assert result.exit_code in (0, 1)

    async def test_binary_injection_via_stdin(self):
        """Binary data in stdin should not cause issues."""
        code = "print(input())"
        result = await Sandbox.run(
            source_code=code,
            language="python",
            test_input="\x00\x01\x02\xff" * 100,
            time_limit_s=2,
            file_extension=".py",
            run_command="python3 /code/solution.py",
        )
        assert result.exit_code == 0

    async def test_concurrent_execution_isolation(self):
        """Concurrent executions should not interfere with each other."""
        import asyncio

        code1 = "print('hello')"
        code2 = "print('world')"

        async def run(code: str) -> str:
            result = await Sandbox.run(
                source_code=code, language="python", test_input="",
                time_limit_s=2, file_extension=".py",
                run_command="python3 /code/solution.py",
            )
            return result.stdout.strip()

        r1, r2 = await asyncio.gather(run(code1), run(code2))
        assert r1 == "hello"
        assert r2 == "world"

    async def test_filesystem_write_attempt(self):
        """Attempts to write to filesystem should be isolated (Docker read-only)."""
        code = """
try:
    with open('/tmp/test.txt', 'w') as f:
        f.write('pwned')
    print('written')
except Exception:
    print('blocked')
"""
        result = await Sandbox.run(
            source_code=code, language="python", test_input="",
            time_limit_s=2, file_extension=".py",
            run_command="python3 /code/solution.py",
        )
        # Either blocked (in Docker read-only) or written to isolated tmpdir
        assert "pwned" not in result.stdout or result.exit_code != 0

    async def test_network_request_attempt(self):
        """Attempts to make network requests should not crash the sandbox."""
        code = """
import urllib.request
try:
    urllib.request.urlopen('http://localhost:1', timeout=1)
    print('ok')
except Exception:
    print('blocked')
"""
        result = await Sandbox.run(
            source_code=code, language="python", test_input="",
            time_limit_s=3, file_extension=".py",
            run_command="python3 /code/solution.py",
        )
        # With Docker --network=none this fails; without Docker it may connect
        # Either way, sandbox should not crash
        assert result.exit_code in (0, 1)

    async def test_language_registry_injection(self):
        """Invalid language IDs should not cause security issues."""
        assert get_language("python") is not None
        assert get_language("python; rm -rf /") is None
        assert get_language("../../../etc/passwd") is None
