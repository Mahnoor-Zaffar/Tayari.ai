"""Base code runner interface.

All language-specific runners inherit from ``CodeRunner``.
The runner handles:
- Writing source code to a temp directory
- Compiling (if applicable)
- Executing against test case inputs
- Capturing stdout, stderr, exit code, timing
"""

from __future__ import annotations

import subprocess
import tempfile
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ExecutionResult:
    """Result of executing a single test case."""

    stdout: str
    stderr: str
    exit_code: int
    execution_ms: int
    timed_out: bool = False
    oom_killed: bool = False
    compiler_output: str = ""


@dataclass
class RunResult:
    """Aggregated result across all test cases."""

    results: list[ExecutionResult]
    total_ms: int
    passed_count: int
    total_count: int
    compiler_output: str = ""


class CodeRunner(ABC):
    """Base class for language-specific code runners."""

    def __init__(self, config) -> None:
        self._config = config

    async def run_code(
        self,
        source_code: str,
        test_inputs: list[str],
        time_limit_s: int = 10,
        memory_limit_mb: int = 256,
    ) -> RunResult:
        """Run the source code against each test input.

        Creates a temporary directory, writes the source file,
        compiles (if needed), and runs each test case.
        """
        results: list[ExecutionResult] = []
        total_start = time.time()

        with tempfile.TemporaryDirectory(prefix="tayari-code-") as tmpdir:
            workdir = Path(tmpdir)
            outdir = workdir / "out"
            outdir.mkdir(exist_ok=True)

            source_path = self._write_source(workdir, source_code)
            compiler_output = ""
            compile_result = self._compile(workdir, source_path)

            if compile_result is not None:
                compiler_output = compile_result.stderr
                if compile_result.exit_code != 0:
                    return RunResult(
                        results=[ExecutionResult(
                            stdout="", stderr=compile_result.stderr,
                            exit_code=compile_result.exit_code, execution_ms=0,
                            compiler_output=compile_result.stderr,
                        )],
                        total_ms=0, passed_count=0, total_count=len(test_inputs),
                        compiler_output=compile_result.stderr,
                    )

            for test_input in test_inputs:
                result = self._execute(
                    workdir, test_input, time_limit_s, memory_limit_mb,
                )
                results.append(result)

        total_ms = int((time.time() - total_start) * 1000)
        passed = sum(1 for r in results if r.exit_code == 0)

        return RunResult(
            results=results, total_ms=total_ms,
            passed_count=passed, total_count=len(test_inputs),
            compiler_output=compiler_output,
        )

    @abstractmethod
    def _write_source(self, workdir: Path, source_code: str) -> Path:
        """Write source code to the working directory.

        Returns the path to the source file.
        """
        ...

    def _compile(self, workdir: Path, source_path: Path) -> ExecutionResult | None:
        """Compile the source code (if applicable).

        Returns None for interpreted languages.
        Returns an ExecutionResult with compile exit code and stderr.
        """
        if self._config.compile_command is None:
            return None

        cmd = self._config.compile_command.replace("/code", str(workdir))
        start = time.time()
        proc = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=self._config.timeout_s,
            cwd=str(workdir),
        )
        elapsed = int((time.time() - start) * 1000)
        return ExecutionResult(
            stdout=proc.stdout, stderr=proc.stderr,
            exit_code=proc.returncode, execution_ms=elapsed,
        )

    def _execute(
        self, workdir: Path, test_input: str,
        time_limit_s: int, memory_limit_mb: int,
    ) -> ExecutionResult:
        """Execute the compiled/interpreted code with the given input."""
        cmd = self._config.run_command.replace("/code", str(workdir))
        start = time.time()
        try:
            proc = subprocess.run(
                cmd, shell=True, input=test_input, capture_output=True,
                text=True, timeout=time_limit_s,
                cwd=str(workdir),
            )
            elapsed = int((time.time() - start) * 1000)
            return ExecutionResult(
                stdout=proc.stdout, stderr=proc.stderr,
                exit_code=proc.returncode, execution_ms=elapsed,
            )
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                stdout="", stderr="Execution timed out",
                exit_code=-1, execution_ms=time_limit_s * 1000,
                timed_out=True,
            )
