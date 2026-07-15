"""Language registry — maps language identifiers to their runner implementations.

Adding a new language requires:
1. Create a runner class in ``execution/runners/``
2. Register it in ``LANGUAGE_REGISTRY``
3. Add the Docker image reference

No business logic changes needed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from execution.runners.base import CodeRunner


@dataclass
class LanguageConfig:
    """Configuration for a supported programming language."""

    id: str
    display_name: str
    runner_class: type[CodeRunner]
    docker_image: str
    file_extension: str
    compile_command: str | None  # None for interpreted languages
    run_command: str
    version_command: str
    timeout_s: int = 10
    memory_limit_mb: int = 256
    default_template: str = ""


from execution.runners.cpp_runner import CppRunner
from execution.runners.go_runner import GoRunner
from execution.runners.java_runner import JavaRunner
from execution.runners.javascript_runner import JavaScriptRunner
from execution.runners.python_runner import PythonRunner
from execution.runners.rust_runner import RustRunner
from execution.runners.typescript_runner import TypeScriptRunner

LANGUAGE_REGISTRY: dict[str, LanguageConfig] = {
    "python": LanguageConfig(
        id="python",
        display_name="Python 3.13",
        runner_class=PythonRunner,
        docker_image="python:3.13-slim",
        file_extension=".py",
        compile_command=None,
        run_command="python3 /code/solution.py",
        version_command="python3 --version",
        timeout_s=10,
    ),
    "javascript": LanguageConfig(
        id="javascript",
        display_name="JavaScript (Node.js 22)",
        runner_class=JavaScriptRunner,
        docker_image="node:22-alpine",
        file_extension=".js",
        compile_command=None,
        run_command="node /code/solution.js",
        version_command="node --version",
        timeout_s=10,
    ),
    "typescript": LanguageConfig(
        id="typescript",
        display_name="TypeScript 5.x (Node.js 22)",
        runner_class=TypeScriptRunner,
        docker_image="node:22-alpine",
        file_extension=".ts",
        compile_command="npx tsc /code/solution.ts --outDir /code/out",
        run_command="node /code/out/solution.js",
        version_command="node --version",
        timeout_s=15,
    ),
    "java": LanguageConfig(
        id="java",
        display_name="Java 21",
        runner_class=JavaRunner,
        docker_image="eclipse-temurin:21-jdk-alpine",
        file_extension=".java",
        compile_command="javac -d /code/out /code/Solution.java",
        run_command="java -cp /code/out Solution",
        version_command="java -version 2>&1",
        timeout_s=15,
        memory_limit_mb=512,
    ),
    "cpp": LanguageConfig(
        id="cpp",
        display_name="C++20 (GCC 14)",
        runner_class=CppRunner,
        docker_image="gcc:14-bookworm",
        file_extension=".cpp",
        compile_command="g++ -std=c++20 -O2 -o /code/out/solution /code/solution.cpp",
        run_command="/code/out/solution",
        version_command="g++ --version",
        timeout_s=15,
        memory_limit_mb=512,
    ),
    "go": LanguageConfig(
        id="go",
        display_name="Go 1.23",
        runner_class=GoRunner,
        docker_image="golang:1.23-alpine",
        file_extension=".go",
        compile_command="go build -o /code/out/solution /code/solution.go",
        run_command="/code/out/solution",
        version_command="go version",
        timeout_s=15,
        memory_limit_mb=512,
    ),
    "rust": LanguageConfig(
        id="rust",
        display_name="Rust 2024 (rustc 1.80)",
        runner_class=RustRunner,
        docker_image="rust:1.80-slim-bookworm",
        file_extension=".rs",
        compile_command="rustc -O -o /code/out/solution /code/solution.rs",
        run_command="/code/out/solution",
        version_command="rustc --version",
        timeout_s=20,
        memory_limit_mb=512,
    ),
}


def get_language(lang_id: str) -> LanguageConfig | None:
    """Return the language config, or None if not found."""
    return LANGUAGE_REGISTRY.get(lang_id)


def get_supported_languages() -> list[dict]:
    """Return a list of supported languages for the API."""
    return [
        {"id": cfg.id, "name": cfg.display_name, "extension": cfg.file_extension}
        for cfg in LANGUAGE_REGISTRY.values()
    ]
