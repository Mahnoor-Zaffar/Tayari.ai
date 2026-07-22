"""Prompt builder for interview sessions.

Loads interviewer and evaluator prompt templates from the prompts package,
interpolates session configuration, and assembles the system prompt.
"""

from __future__ import annotations

from pathlib import Path

PROMPTS_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent / "packages" / "prompts"

INTERVIEWER_DIR = PROMPTS_ROOT / "interviewers"
EVALUATOR_DIR = PROMPTS_ROOT / "evaluators"
TEMPLATE_DIR = PROMPTS_ROOT / "templates" / "company-specific"


class PromptBuilder:
    """Loads, interpolates, and assembles interview prompts.

    Caches compiled prompts by config hash to avoid redundant
    file I/O and interpolation for identical configurations.
    """

    def __init__(self) -> None:
        self._cache: dict[int, str] = {}

    def _config_hash(self, **kwargs: str | None) -> int:
        return hash(frozenset((k, v or "") for k, v in kwargs.items()))

    def _interpolate(self, template: str, **kwargs: str) -> str:
        """Safely interpolate template variables using plain string replacement.

        Avoids Python's ``.format()`` to prevent KeyError from JSON braces
        in prompt templates (e.g., evaluator prompts with ``{...}`` JSON).
        """
        result = template
        for key, value in kwargs.items():
            result = result.replace(f"{{{key}}}", value)
        return result

    def build_system_prompt(
        self,
        interview_type: str,
        company: str,
        role: str,
        experience_level: str,
        language: str | None = None,
        framework: str | None = None,
        difficulty: str | None = None,
        duration_minutes: int = 30,
        spoken_language: str | None = "en",
        system_design_problem: str | None = None,
        resume_context: str | None = None,
        jd_context: str | None = None,
        custom_instructions: str | None = None,
    ) -> str:
        """Build the complete system prompt for the AI interviewer.

        1. Check cache for this config.
        2. Load the interviewer prompt for the interview type.
        3. Interpolate configuration variables.
        4. Append company-specific instructions if available.
        5. Append resume/JD context if provided.
        6. Append custom instructions if provided.
        """
        cache_key = self._config_hash(
            interview_type=interview_type,
            company=company,
            role=role,
            experience_level=experience_level,
            language=language,
            framework=framework,
            difficulty=difficulty,
            duration_minutes=str(duration_minutes),
            spoken_language=spoken_language,
            system_design_problem=system_design_problem,
            resume_context=resume_context,
            jd_context=jd_context,
            custom_instructions=custom_instructions,
        )
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        base = self._load_interviewer_prompt(interview_type)
        company_prompt = self._load_company_template(company)

        # Determine system design problem and missing aspect
        problem = system_design_problem or "a scalable system relevant to the role"
        missing_aspect = self._derive_missing_aspect(problem)

        parts: list[str] = []

        # Base interviewer prompt with safe interpolation
        interpolated = self._interpolate(
            base,
            company=company,
            role=role,
            level=experience_level,
            language=language or "",
            framework=framework or "",
            difficulty=difficulty or "medium",
            duration_minutes=str(duration_minutes),
            spoken_language=spoken_language or "en",
            problem=problem,
            missing_aspect=missing_aspect,
        )
        parts.append(interpolated)

        # Company-specific instructions
        if company_prompt:
            parts.append(f"\n## Company Context\n{company_prompt}")

        # Resume context
        if resume_context:
            parts.append(f"\n## Candidate Background\n{resume_context}")

        # Job description context
        if jd_context:
            parts.append(f"\n## Target Role Context\n{jd_context}")

        # Custom instructions
        if custom_instructions:
            parts.append(f"\n## Custom Instructions\n{custom_instructions}")

        result = "\n\n".join(parts)
        if cache_key is not None:
            self._cache[cache_key] = result
        return result

    def build_evaluator_prompt(
        self,
        interview_type: str,
        company: str,
        role: str,
        experience_level: str,
        language: str | None = None,
        difficulty: str | None = None,
        framework: str | None = None,
    ) -> str:
        """Build the evaluator prompt for post-interview evaluation."""
        base = self._load_evaluator_prompt(interview_type)
        return self._interpolate(
            base,
            company=company,
            role=role,
            level=experience_level,
            language=language or "",
            difficulty=difficulty or "medium",
            framework=framework or "",
        )

    def _load_interviewer_prompt(self, interview_type: str) -> str:
        path = INTERVIEWER_DIR / f"{interview_type}.md"
        if not path.exists():
            msg = f"Interviewer prompt not found: {path}"
            raise FileNotFoundError(msg)
        return path.read_text(encoding="utf-8")

    def _load_evaluator_prompt(self, interview_type: str) -> str:
        path = EVALUATOR_DIR / f"{interview_type}.md"
        if not path.exists():
            msg = f"Evaluator prompt not found: {path}"
            raise FileNotFoundError(msg)
        return path.read_text(encoding="utf-8")

    def _load_company_template(self, company: str) -> str | None:
        company_lower = company.lower().replace(" ", "-")
        path = TEMPLATE_DIR / f"{company_lower}.md"
        if path.exists():
            return path.read_text(encoding="utf-8")
        return None

    def get_supported_interview_types(self) -> list[str]:
        """Return interview types that have prompt files."""
        if not INTERVIEWER_DIR.exists():
            return []
        return [p.stem for p in sorted(INTERVIEWER_DIR.glob("*.md"))]

    def _derive_missing_aspect(self, problem: str) -> str:
        """Return a plausible missing aspect to probe for system design problems."""
        problem_lower = problem.lower()
        if "database" in problem_lower or "storage" in problem_lower or "sql" in problem_lower:
            return "failure recovery and replication"
        if "cache" in problem_lower or "redis" in problem_lower:
            return "cache invalidation and consistency"
        if "message" in problem_lower or "queue" in problem_lower or "kafka" in problem_lower:
            return "message ordering and dead-letter handling"
        if "api" in problem_lower or "gateway" in problem_lower or "load" in problem_lower:
            return "rate limiting and circuit breakers"
        if "auth" in problem_lower or "login" in problem_lower or "session" in problem_lower:
            return "token expiry and session revocation"
        return "scalability under load"
