"""C++ runner — compiles with g++, runs the binary."""

from __future__ import annotations

from pathlib import Path

from execution.runners.base import CodeRunner


class CppRunner(CodeRunner):
    def _write_source(self, workdir: Path, source_code: str) -> Path:
        path = workdir / "solution.cpp"
        path.write_text(self._ensure_main(source_code))
        return path

    def _ensure_main(self, code: str) -> str:
        if "#include" not in code:
            code = "#include <iostream>\n#include <string>\nusing namespace std;\n" + code
        if "int main" not in code:
            code += "\nint main() {\n    string line;\n    while (getline(cin, line)) {\n        cout << solve(line) << endl;\n    }\n    return 0;\n}\n"
        return code
