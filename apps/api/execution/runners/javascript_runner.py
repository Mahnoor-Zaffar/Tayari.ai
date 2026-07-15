"""JavaScript runner — interpreted via Node.js."""

from __future__ import annotations

from pathlib import Path

from execution.runners.base import CodeRunner


class JavaScriptRunner(CodeRunner):
    def _write_source(self, workdir: Path, source_code: str) -> Path:
        path = workdir / "solution.js"
        path.write_text(source_code)
        return path
