"""Code execution service — orchestrates the execution pipeline."""

from __future__ import annotations

import time
import uuid
from uuid import UUID

from execution.judge import judge_test_cases
from execution.logger import log_execution
from execution.registry import get_language, get_supported_languages
from execution.sandbox import Sandbox, SandboxResult
from features.code.repository import CodeRepository
from features.code.schemas import RunCodeResponse


class CodeExecutionService:
    """Service for code execution and submission management."""

    def __init__(self, repo: CodeRepository) -> None:
        self._repo = repo

    async def run_code(
        self,
        language: str,
        source_code: str,
        test_input: str = "",
    ) -> RunCodeResponse:
        """Execute code once and return the result.

        Used for the "Run" button during development — no persistence.
        """
        config = get_language(language)
        if config is None:
            raise ValueError(f"Unsupported language: {language}")

        result = await Sandbox.run(
            source_code=source_code,
            language=language,
            test_input=test_input,
            file_extension=config.file_extension,
            run_command=config.run_command,
            compile_command=config.compile_command,
            time_limit_s=config.timeout_s,
            memory_limit_mb=config.memory_limit_mb,
        )

        return RunCodeResponse(
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.exit_code,
            execution_ms=result.execution_ms,
            timed_out=result.timed_out,
        )

    async def submit_code(
        self,
        interview_id: UUID,
        user_id: UUID,
        language: str,
        source_code: str,
        test_inputs: list[str] | None = None,
    ) -> dict:
        """Submit code for the full test suite.

        Persists the submission, runs each test case, and returns results.
        """
        config = get_language(language)
        if config is None:
            raise ValueError(f"Unsupported language: {language}")

        submission_id = uuid.uuid4()
        await self._repo.create_submission({
            "id": submission_id,
            "interview_id": interview_id,
            "user_id": user_id,
            "language": language,
            "source_code": source_code,
            "status": "running",
        })

        log_execution(str(submission_id), language, "started")
        test_inputs = test_inputs or [""]

        results: list[SandboxResult] = []
        compiler_output = ""

        for i, test_input in enumerate(test_inputs):
            result = await Sandbox.run(
                source_code=source_code,
                language=language,
                test_input=test_input,
                file_extension=config.file_extension,
                run_command=config.run_command,
                compile_command=config.compile_command,
                time_limit_s=config.timeout_s,
                memory_limit_mb=config.memory_limit_mb,
            )
            results.append(result)
            if i == 0 and result.stderr:
                compiler_output = result.stderr

        # Judge test results
        test_case_dicts = [
            {"id": str(i), "input": ti, "expected_output": "", "is_hidden": False}
            for i, ti in enumerate(test_inputs)
        ]
        actual_outputs = {str(i): r.stdout for i, r in enumerate(results)}

        judged = judge_test_cases(test_case_dicts, actual_outputs)

        status = "completed"
        total_ms = sum(r.execution_ms for r in results)
        stderr = "\n".join(r.stderr for r in results if r.stderr).strip()

        await self._repo.update_submission(submission_id, {
            "status": status,
            "test_results": judged["results"],
            "passed_count": judged["overall_passed"],
            "total_count": judged["overall_total"],
            "execution_ms": total_ms,
            "stdout": "\n".join(r.stdout for r in results if r.stdout).strip(),
            "stderr": stderr or None,
            "compiler_output": compiler_output or None,
            "completed_at": time.time(),
        })

        log_execution(str(submission_id), language, "completed", execution_ms=total_ms)

        return {
            "submission_id": str(submission_id),
            "status": status,
            "passed_count": judged["overall_passed"],
            "total_count": judged["overall_total"],
            "test_results": [
                {
                    "passed": r["passed"],
                    "is_hidden": r["is_hidden"],
                    "actual_output": r.get("actual_output"),
                }
                for r in judged["results"]
            ],
            "execution_ms": total_ms,
            "compiler_output": compiler_output or None,
        }

    async def get_submission_result(self, submission_id: UUID, user_id: UUID) -> dict | None:
        submission = await self._repo.get_submission(submission_id, user_id)
        if submission is None:
            return None
        return {
            "submission_id": str(submission.id),
            "status": submission.status,
            "language": submission.language,
            "passed_count": submission.passed_count,
            "total_count": submission.total_count,
            "execution_ms": submission.execution_ms,
            "test_results": [
                {
                    "passed": tr.get("passed", False),
                    "is_hidden": tr.get("is_hidden", False),
                    "actual_output": tr.get("actual_output"),
                }
                for tr in (submission.test_results or [])
            ],
            "compiler_output": submission.compiler_output,
            "stdout": submission.stdout,
            "stderr": submission.stderr,
            "created_at": submission.created_at,
            "completed_at": submission.completed_at,
        }

    def get_languages(self) -> list[dict]:
        return get_supported_languages()
