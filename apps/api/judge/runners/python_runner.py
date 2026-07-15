"""Python runner — interpreted, no compile step."""

from __future__ import annotations

from pathlib import Path

from judge.runners.base import CodeRunner


class PythonRunner(CodeRunner):
    def _write_source(self, workdir: Path, source_code: str) -> Path:
        path = workdir / "solution.py"
        path.write_text(self._wrap_code(source_code))
        return path

    def _wrap_code(self, code: str) -> str:
        """Wrap code to read from stdin and print output."""
        if "input()" in code or "sys.stdin" in code:
            return code
        if "def " in code and "print" in code:
            return code
        return code
