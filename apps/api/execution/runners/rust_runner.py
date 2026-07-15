"""Rust runner — compiles with rustc, runs the binary."""

from __future__ import annotations

from pathlib import Path

from execution.runners.base import CodeRunner


class RustRunner(CodeRunner):
    def _write_source(self, workdir: Path, source_code: str) -> Path:
        path = workdir / "solution.rs"
        path.write_text(self._ensure_main(source_code))
        return path

    def _ensure_main(self, code: str) -> str:
        if "fn main" not in code:
            code = "use std::io::{self, BufRead};\n\n" + code
            code += "\n\nfn main() {\n    let stdin = io::stdin();\n    for line in stdin.lock().lines() {\n        if let Ok(l) = line {\n            println!(\"{}\", solve(&l));\n        }\n    }\n}\n"
        return code
