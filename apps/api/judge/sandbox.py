"""Execution sandbox — runs code in isolated Docker containers.

Falls back to a plain subprocess when Docker is unavailable. That fallback is a
development/test convenience ONLY and provides **no isolation** (no memory cap,
no CPU cap, no filesystem or network confinement beyond a temp working dir), so
in production the sandbox refuses to run when Docker is absent.

Security:
    - Never uses ``shell=True`` (prevents command injection)
    - Code written to temp file, executed via explicit path
    - Docker: read-only FS, no network, no privileges, PID limit, memory cap
    - Subprocess fallback (dev/test only): NOT isolated — the process runs with
      the API's own privileges and ``memory_limit_mb`` is not enforced
    - Output truncated to prevent memory exhaustion
"""

from __future__ import annotations

import logging
import os
import shlex
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from core.config import settings
from core.errors import InternalError

logger = logging.getLogger(__name__)

SANDBOX_TIMEOUT_S = 30
SANDBOX_MEMORY_MB = 256
SANDBOX_MAX_OUTPUT_CHARS = 100_000
SANDBOX_MAX_EXECUTORS = 10


def _docker_available() -> bool:
    """Check if Docker daemon is reachable on this system."""
    try:
        proc = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return proc.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def _should_use_docker() -> bool:
    """Whether the Docker sandbox is active for this process.

    ``TAYARI_SANDBOX_USE_DOCKER`` (1/true/yes/on) overrides autodetection so
    the test suite can force the unisolated subprocess fallback even on CI
    runners that ship Docker but lack the prebuilt ``tayari-runner-*`` images.
    """
    flag = os.environ.get("TAYARI_SANDBOX_USE_DOCKER")
    if flag is not None:
        return flag.strip().lower() in ("1", "true", "yes", "on")
    return _docker_available()


@dataclass
class SandboxResult:
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    timed_out: bool = False
    oom_killed: bool = False
    execution_ms: int = 0

    def __post_init__(self) -> None:
        self.stdout = self.stdout[:SANDBOX_MAX_OUTPUT_CHARS]
        self.stderr = self.stderr[:SANDBOX_MAX_OUTPUT_CHARS]


class Sandbox:
    """Isolated execution environment for untrusted code.

    Uses Docker when available. When Docker is unavailable it falls back to a
    plain subprocess **with no isolation** — permitted in development/test only.
    In production a missing Docker daemon is a hard failure rather than a silent
    downgrade to unsandboxed execution.
    """

    USE_DOCKER = _should_use_docker()

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

        Raises:
            InternalError: in production when Docker is unavailable, so untrusted
                code is never executed through the unisolated subprocess path.
        """
        if cls.USE_DOCKER:
            return await cls._run_docker(
                source_code,
                language,
                test_input,
                time_limit_s,
                memory_limit_mb,
                file_extension,
                run_command,
                compile_command,
            )

        if settings.is_production:
            logger.error(
                "Refusing to execute code: Docker sandbox unavailable in production "
                "(language=%s). The unisolated subprocess fallback is disabled outside dev/test.",
                language,
            )
            raise InternalError("Code execution is temporarily unavailable")

        return await cls._run_subprocess(
            source_code,
            test_input,
            time_limit_s,
            memory_limit_mb,
            file_extension,
            run_command,
            compile_command,
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
                "docker",
                "run",
                "--rm",
                "--network",
                "none",
                "--read-only",
                "--tmpfs",
                "/tmp:rw,size=32m",
                "--cap-drop=ALL",
                "--security-opt",
                "no-new-privileges",
                "--pids-limit",
                "50",
                "-m",
                f"{memory_limit_mb}m",
                "--memory-swap",
                f"{memory_limit_mb}m",
                "-v",
                f"{workdir}:/code:ro",
                "-v",
                f"{outdir}:/code/out:rw",
                image,
                "sh",
                "-c",
                f"{compile_command + ' && ' if compile_command else ''}{run_command}",
            ]

            start = time.time()
            try:
                proc = subprocess.run(
                    cmd,
                    input=test_input,
                    capture_output=True,
                    text=True,
                    timeout=time_limit_s,
                )
                elapsed = int((time.time() - start) * 1000)
                stderr = proc.stderr
                if proc.returncode != 0 and "pull access denied" in stderr:
                    stderr = (
                        f"Code execution unavailable: missing sandbox image '{image}'. "
                        "The judge requires a prebuilt runner image for this language."
                    )
                return SandboxResult(
                    stdout=proc.stdout,
                    stderr=stderr,
                    exit_code=proc.returncode,
                    execution_ms=elapsed,
                )
            except subprocess.TimeoutExpired:
                return SandboxResult(
                    stderr="Execution timed out",
                    exit_code=-1,
                    timed_out=True,
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
        """Execute code using a plain subprocess (dev/test fallback only).

        Provides **no isolation**: ``memory_limit_mb`` is not enforced, the
        process shares the API's privileges, and only a wall-clock timeout and a
        temp working directory bound it. Guarded by ``run()`` so it never
        executes in production. Uses explicit command paths — never ``shell=True``.
        """
        with tempfile.TemporaryDirectory(prefix="tayari-code-") as tmpdir:
            workdir = Path(tmpdir)
            source_file = workdir / f"solution{file_extension}"
            source_file.write_text(source_code)

            outdir = workdir / "out"
            outdir.mkdir(exist_ok=True)

            if compile_command:
                compile_parts = cls._safe_command(
                    compile_command,
                    workdir,
                    outdir,
                )
                start = time.time()
                try:
                    proc = subprocess.run(
                        compile_parts,
                        capture_output=True,
                        text=True,
                        timeout=time_limit_s,
                        cwd=str(workdir),
                    )
                except subprocess.TimeoutExpired:
                    return SandboxResult(
                        stderr="Compilation timed out",
                        exit_code=-1,
                        timed_out=True,
                    )
                if proc.returncode != 0:
                    return SandboxResult(
                        stderr=proc.stderr,
                        exit_code=proc.returncode,
                    )

            run_parts = cls._safe_command(
                run_command,
                workdir,
                outdir,
            )
            start = time.time()
            try:
                proc = subprocess.run(
                    run_parts,
                    input=test_input,
                    capture_output=True,
                    text=True,
                    timeout=time_limit_s,
                    cwd=str(workdir),
                )
                elapsed = int((time.time() - start) * 1000)
                return SandboxResult(
                    stdout=proc.stdout,
                    stderr=proc.stderr,
                    exit_code=proc.returncode,
                    execution_ms=elapsed,
                )
            except subprocess.TimeoutExpired:
                return SandboxResult(
                    stderr="Execution timed out",
                    exit_code=-1,
                    timed_out=True,
                    execution_ms=time_limit_s * 1000,
                )

    @staticmethod
    def _safe_command(cmd: str, workdir: Path, outdir: Path) -> list[str]:
        """Convert a shell command string to a safe list of args.

        Replaces /code/out before /code so the output-dir placeholder is not
        swallowed by the source-dir replacement, then splits using shlex to
        preserve quoted paths.
        """
        cmd = cmd.replace("/code/out", str(outdir)).replace("/code", str(workdir))
        return shlex.split(cmd)
