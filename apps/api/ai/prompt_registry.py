"""Unified, versioned prompt registry.

Single source for loading interview, evaluator, and company-specific prompt
templates across the platform.  Interview/evaluator templates live in the
``packages/prompts`` workspace; the registry adds versioned caching and a
fallback to built-in defaults for evaluator prompts so a missing file degrades
gracefully instead of raising.
"""

from __future__ import annotations

from pathlib import Path

PROMPTS_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent / "packages" / "prompts"

INTERVIEWER_DIR = PROMPTS_ROOT / "interviewers"
EVALUATOR_DIR = PROMPTS_ROOT / "evaluators"
TEMPLATE_DIR = PROMPTS_ROOT / "templates" / "company-specific"


class PromptRegistry:
    """Loads and caches prompt templates by kind, interview type, and version."""

    def __init__(self) -> None:
        self._cache: dict[str, str] = {}

    def get_interview_prompt(self, interview_type: str, version: str = "v1") -> str:
        """Return the interviewer template for a type. Raises if unavailable."""
        key = f"interview:{interview_type}:{version}"
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        path = INTERVIEWER_DIR / f"{interview_type}.md"
        if not path.exists():
            msg = f"Interviewer prompt not found: {path}"
            raise FileNotFoundError(msg)
        template = path.read_text(encoding="utf-8")
        self._cache[key] = template
        return template

    def get_evaluator_prompt(self, interview_type: str, version: str = "v1") -> str:
        """Return the evaluator template for a type.

        Prefers the workspace ``evaluators/{type}.md`` file; falls back to the
        built-in evaluation prompt registry so a missing file degrades
        gracefully.
        """
        key = f"evaluator:{interview_type}:{version}"
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        path = EVALUATOR_DIR / f"{interview_type}.md"
        if path.exists():
            template = path.read_text(encoding="utf-8")
        else:
            from evaluation.prompt_registry import PromptRegistry as EvalPromptRegistry

            template = EvalPromptRegistry().get_prompt(interview_type, version)

        self._cache[key] = template
        return template

    def get_company_template(self, company: str) -> str | None:
        """Return a company-specific template or None if none exists."""
        company_lower = company.lower().replace(" ", "-")
        path = TEMPLATE_DIR / f"{company_lower}.md"
        if not path.exists():
            return None
        key = f"company:{company_lower}"
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        template = path.read_text(encoding="utf-8")
        self._cache[key] = template
        return template
