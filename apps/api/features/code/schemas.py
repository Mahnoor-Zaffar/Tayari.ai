"""Pydantic schemas for the coding interview feature."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class RunCodeRequest(BaseModel):
    """POST /code/run body — execute code once and return output."""

    language: str = Field(min_length=1, max_length=20)
    source_code: str = Field(min_length=1, max_length=50000)
    test_input: str = Field(default="", max_length=10000)


class RunCodeResponse(BaseModel):
    """Result of a code execution."""

    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    execution_ms: int = 0
    timed_out: bool = False


class SubmitCodeRequest(BaseModel):
    """POST /code/submit body — submit code for full test suite execution."""

    interview_id: UUID
    language: str = Field(min_length=1, max_length=20)
    source_code: str = Field(min_length=1, max_length=50000)
    test_inputs: list[str] = Field(default_factory=list)
    problem_id: UUID | None = None


class SubmitCodeResponse(BaseModel):
    """Submission confirmation."""

    submission_id: UUID
    status: str = "queued"


class TestResult(BaseModel):
    """Result of a single test case."""

    passed: bool
    is_hidden: bool = False
    actual_output: str | None = None


class SubmissionResultResponse(BaseModel):
    """Full submission result."""

    submission_id: UUID
    status: str
    language: str
    passed_count: int = 0
    total_count: int = 0
    execution_ms: int | None = None
    test_results: list[TestResult] = []
    compiler_output: str | None = None
    stdout: str | None = None
    stderr: str | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None


class LanguageInfo(BaseModel):
    """Supported language information."""

    id: str
    name: str
    extension: str


class ProblemSummary(BaseModel):
    """Lightweight problem info for listing."""

    id: UUID
    slug: str
    title: str
    difficulty: str


class Example(BaseModel):
    input: str
    output: str
    explanation: str | None = None


class VisibleTestCase(BaseModel):
    """A non-hidden test case shown to the user (with its expected output)."""

    id: str
    input: str
    expected_output: str


class ProblemDetail(BaseModel):
    """Full problem details for the editor panel.

    Hidden test cases are never included — they are only evaluated server-side.
    """

    id: UUID
    slug: str
    title: str
    difficulty: str
    description: str
    examples: list[Example] = []
    constraints: list[str] = []
    test_cases: list[VisibleTestCase] = []
    total_test_count: int = 0
    hidden_test_count: int = 0
