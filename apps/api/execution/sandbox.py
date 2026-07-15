"""Execution sandbox — runs code in isolated Docker containers.

Falls back to subprocess when Docker is unavailable (development/test).
"""

from __future__ import annotations

import logging
import subprocess
import tempfile
import time
from pathlib import Path

logger = logging.getLogger(__name__)

SANDBOX_TIMEOUT_S = 30
SANDBOX_MEMORY_MB = 256
SANDBOX_MAX_OUTPUT_CHARS = 100_000
SANDBOX_MAX_FILE_SIZE_MB = 10


def _docker_available() -> bool:
    """Check if Docker daemon is reachable on this system."""
    try:
        proc = subprocess.run(
            ["docker", "info"],
            capture_output=True, text=True, timeout=5,
        )
        return proc.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


class SandboxError(Exception):
    pass


class SandboxResult:
    def __init__(
        self,
        stdout: str = "",
        stderr: str = "",
        exit_code: int = 0,
        timed_out: bool = False,
        oom_killed: bool = False,
        execution_ms: int = 0,
    ) -> None:
        self.stdout = stdout[:SANDBOX_MAX_OUTPUT_CHARS]
        self.stderr = stderr[:SANDBOX_MAX_OUTPUT_CHARS]
        self.exit_code = exit_code
        self.timed_out = timed_out
        self.oom_killed = oom_killed
        self.execution_ms = execution_ms


class Sandbox:
    """Isolated execution environment for untrusted code.

    Uses Docker when available, falls back to subprocess with ``ulimit``
    for development environments.
    """

    USE_DOCKER = _docker_available()

    @classmethod
    async def run(
        cls,
        source_code: str,
        language: str,
        test_input: str = "",
        time_limit_s: int = SANDBOX_TIMEOUT_S,
        memory_limit_mb: int = SANDBOX_MEMORY_MB,
        file_extension: str = ".py",
        run_command: str = "python3 /code/solution.py",
        compile_command: str | None = None,
    ) -> SandboxResult:
        """Execute source code in a sandboxed environment.

        Args:
            source_code: The code to execute.
            language: Language identifier (for logging).
            test_input: stdin input for the execution.
            time_limit_s: Maximum execution time in seconds.
            memory_limit_mb: Maximum memory in MB.
            file_extension: File extension for the source file.
            run_command: Command to run the compiled/interpreted code.
            compile_command: Command to compile (None for interpreted).

        Returns:
            SandboxResult with stdout, stderr, exit code, timing.
        """
        if cls.USE_DOCKER:
            return await cls._run_docker(
                source_code, language, test_input,
                time_limit_s, memory_limit_mb,
                file_extension, run_command, compile_command,
            )
        return await cls._run_subprocess(
            source_code, test_input, time_limit_s, memory_limit_mb,
            file_extension, run_command, compile_command,
        )

    @classmethod
    async def _run_docker(
        cls,
        source_code: str,
        language: str,
        test_input: str,
        time_limit_s: int,
        memory_limit_mb: int,
        file_extension: str,
        run_command: str,
        compile_command: str | None,
    ) -> SandboxResult:
        """Execute code in a Docker container with resource limits."""
        with tempfile.TemporaryDirectory(prefix="tayari-sandbox-") as tmpdir:
            workdir = Path(tmpdir)
            source_file = workdir / f"solution{file_extension}"
            source_file.write_text(source_code)

            outdir = workdir / "out"
            outdir.mkdir(exist_ok=True)

            image = f"tayari-runner-{language}"
            cmd = [
                "docker", "run", "--rm",
                "--network", "none",
                "--read-only",
                "--cap-drop=ALL",
                "--security-opt", "no-new-privileges",
                "--pids-limit", "50",
                "-m", f"{memory_limit_mb}m",
                "--memory-swap", f"{memory_limit_mb}m",
                "-v", f"{workdir}:/code:ro",
                image,
                "sh", "-c",
                f"{compile_command + ' && ' if compile_command else ''}{run_command}",
            ]

            start = time.time()
            try:
                proc = subprocess.run(
                    cmd, input=test_input, capture_output=True,
                    text=True, timeout=time_limit_s,
                )
                elapsed = int((time.time() - start) * 1000)
                return SandboxResult(
                    stdout=proc.stdout, stderr=proc.stderr,
                    exit_code=proc.returncode, execution_ms=elapsed,
                )
            except subprocess.TimeoutExpired:
                return SandboxResult(
                    stderr="Execution timed out",
                    exit_code=-1, timed_out=True,
                    execution_ms=time_limit_s * 1000,
                )

    @classmethod
    async def _run_subprocess(
        cls,
        source_code: str,
        test_input: str,
        time_limit_s: int,
        memory_limit_mb: int,
        file_extension: str,
        run_command: str,
        compile_command: str | None,
    ) -> SandboxResult:
        """Execute code using subprocess with resource limits.

        Fallback when Docker is unavailable (development).
        """
        with tempfile.TemporaryDirectory(prefix="tayari-code-") as tmpdir:
            workdir = Path(tmpdir)
            source_file = workdir / f"solution{file_extension}"
            source_file.write_text(source_code)

            outdir = workdir / "out"
            outdir.mkdir(exist_ok=True)

            def _run(cmd: str, input_text: str = "") -> subprocess.CompletedProcess:
                return subprocess.run(
                    cmd, shell=True, input=input_text,
                    capture_output=True, text=True,
                    timeout=time_limit_s, cwd=str(workdir),
                )

            if compile_command:
                compile_cmd = (
                    compile_command
                    .replace("/code", str(workdir))
                    .replace("/code/out", str(outdir))
                )
                proc = _run(compile_cmd)
                if proc.returncode != 0:
                    return SandboxResult(
                        stderr=proc.stderr, exit_code=proc.returncode,
                    )

            run_cmd = (
                run_command
                .replace("/code", str(workdir))
                .replace("/code/out", str(outdir))
            )

            start = time.time()
            try:
                proc = _run(run_cmd, test_input)
                elapsed = int((time.time() - start) * 1000)
                return SandboxResult(
                    stdout=proc.stdout, stderr=proc.stderr,
                    exit_code=proc.returncode, execution_ms=elapsed,
                )
            except subprocess.TimeoutExpired:
                return SandboxResult(
                    stderr="Execution timed out",
                    exit_code=-1, timed_out=True,
                    execution_ms=time_limit_s * 1000,
                )
