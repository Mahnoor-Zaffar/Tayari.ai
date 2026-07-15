"""Go runner — compiles with go build, runs the binary."""

from __future__ import annotations

from pathlib import Path

from execution.runners.base import CodeRunner


class GoRunner(CodeRunner):
    def _write_source(self, workdir: Path, source_code: str) -> Path:
        path = workdir / "solution.go"
        path.write_text(self._ensure_package(source_code))
        return path

    def _ensure_package(self, code: str) -> str:
        if "package main" not in code:
            code = "package main\n\n" + code
        if "func main" not in code and "func main()" not in code:
            code += "\n\nfunc main() {\n    var input string\n    fmt.Scanln(&input)\n    fmt.Println(solve(input))\n}\n"
        if "import" not in code and ("fmt" in code or "os" in code):
            code = code.replace("package main\n", "package main\n\nimport \"fmt\"\n")
        return code
