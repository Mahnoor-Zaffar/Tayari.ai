"""Java runner — compiles with javac, runs with java.

Expects a class named ``Solution`` with a ``main`` method.
"""

from __future__ import annotations

from pathlib import Path

from execution.runners.base import CodeRunner


class JavaRunner(CodeRunner):
    def _write_source(self, workdir: Path, source_code: str) -> Path:
        path = workdir / "Solution.java"
        path.write_text(self._ensure_public_class(source_code))
        return path

    def _ensure_public_class(self, code: str) -> str:
        if "public class Solution" not in code and "class Solution" not in code:
            return f"public class Solution {{\n    public static void main(String[] args) throws Exception {{\n{code}\n    }}\n}}"
        return code
