"""Prompt Registry — versioned evaluation prompts.

Loads prompts from the ``prompts/`` subdirectory or falls back to
default templates.  Supports version pinning for A/B testing.
"""

from __future__ import annotations

from pathlib import Path

PROMPT_DIR = Path(__file__).resolve().parent / "prompts"

DEFAULT_EVALUATOR_PROMPTS: dict[str, str] = {
    "coding": (
        "You are an expert technical interview evaluator. "
        "Review the following coding interview transcript and candidate code. "
        "Produce a structured evaluation.\n\n"
        "## Candidate Context\n"
        "- Target Company: {company}\n"
        "- Role: {role}\n"
        "- Experience Level: {level}\n"
        "- Language: {language}\n\n"
        "## Transcript\n{transcript}\n\n"
        "## Code Submission\n{code_submission}\n\n"
        "## Test Results\n{test_results}\n\n"
        "## Evaluation Dimensions\n"
        "- correctness (weight 30%): Does the code compile? Pass tests? Handle edge cases?\n"
        "- efficiency (weight 20%): Is time/space complexity optimal?\n"
        "- code_quality (weight 20%): Readable? Well-structured? Idiomatic?\n"
        "- technical_communication (weight 15%): Explains approach clearly?\n"
        "- language_proficiency (weight 15%): Fluent in language? Uses stdlib?\n\n"
        "## Per-Question Scoring\n"
        "For each question/answer pair in the transcript, evaluate the candidate's response "
        "on each dimension. Include the question text, answer text, scores, and brief feedback.\n\n"
        "## Output Format\n"
        "Return ONLY valid JSON with no markdown fences:\n"
        '{{"overall_score": <0.0-5.0>, '
        '"dimensions": {{"correctness": {{"score": <0.0-5.0>, "evidence": "..."}}, '
        '"efficiency": {{"score": <0.0-5.0>, "evidence": "..."}}, '
        '"code_quality": {{"score": <0.0-5.0>, "evidence": "..."}}, '
        '"technical_communication": {{"score": <0.0-5.0>, "evidence": "..."}}, '
        '"language_proficiency": {{"score": <0.0-5.0>, "evidence": "..."}}}}, '
        '"question_scores": [{{"question_index": 0, "question_text": "...", "answer_text": "...", '
        '"dimension_scores": {{"correctness": {{"score": <0.0-5.0>, "evidence": "..."}}, '
        '"efficiency": {{"score": <0.0-5.0>, "evidence": "..."}}, '
        '"code_quality": {{"score": <0.0-5.0>, "evidence": "..."}}, '
        '"technical_communication": {{"score": <0.0-5.0>, "evidence": "..."}}, '
        '"language_proficiency": {{"score": <0.0-5.0>, "evidence": "..."}}}}, '
        '"overall_score": <0.0-5.0>, "feedback": "..."}}], '
        '"strengths": ["..."], "improvements": ["..."], '
        '"recommendations": ["..."], "confidence": <0.0-1.0>}}'
    ),
    "system-design": (
        "You are an expert system design interview evaluator. "
        "Review the following transcript and produce a structured evaluation.\n\n"
        "## Candidate Context\n"
        "- Target Company: {company}\n"
        "- Role: {role}\n"
        "- Experience Level: {level}\n\n"
        "## Transcript\n{transcript}\n\n"
        "## Evaluation Dimensions\n"
        "- requirements_gathering (weight 20%): Clarified scope and constraints?\n"
        "- architecture (weight 30%): Sound high-level design?\n"
        "- trade_off_analysis (weight 30%): Justified choices, compared alternatives?\n"
        "- communication (weight 20%): Clear, structured explanation?\n\n"
        "## Per-Question Scoring\n"
        "For each question/answer pair in the transcript, evaluate the candidate's response "
        "on each dimension. Include the question text, answer text, scores, and brief feedback.\n\n"
        "## Output Format\n"
        "Return ONLY valid JSON with no markdown fences:\n"
        '{{"overall_score": <0.0-5.0>, '
        '"dimensions": {{"requirements_gathering": {{"score": <0.0-5.0>, "evidence": "..."}}, '
        '"architecture": {{"score": <0.0-5.0>, "evidence": "..."}}, '
        '"trade_off_analysis": {{"score": <0.0-5.0>, "evidence": "..."}}, '
        '"communication": {{"score": <0.0-5.0>, "evidence": "..."}}}}, '
        '"question_scores": [{{"question_index": 0, "question_text": "...", "answer_text": "...", '
        '"dimension_scores": {{"requirements_gathering": {{"score": <0.0-5.0>, "evidence": "..."}}, '
        '"architecture": {{"score": <0.0-5.0>, "evidence": "..."}}, '
        '"trade_off_analysis": {{"score": <0.0-5.0>, "evidence": "..."}}, '
        '"communication": {{"score": <0.0-5.0>, "evidence": "..."}}}}, '
        '"overall_score": <0.0-5.0>, "feedback": "..."}}], '
        '"strengths": ["..."], "improvements": ["..."], '
        '"recommendations": ["..."], "confidence": <0.0-1.0>}}'
    ),
    "behavioral": (
        "You are an expert behavioral interview evaluator. "
        "Review the following transcript and produce a structured evaluation.\n\n"
        "## Candidate Context\n"
        "- Target Company: {company}\n"
        "- Role: {role}\n"
        "- Experience Level: {level}\n\n"
        "## Transcript\n{transcript}\n\n"
        "## Evaluation Dimensions\n"
        "- structure_star (weight 30%): Situation → Task → Action → Result?\n"
        "- relevance (weight 25%): Answer directly addresses the question?\n"
        "- specificity (weight 25%): Concrete details vs. vague generalities?\n"
        "- impact (weight 20%): Measurable outcomes, growth demonstrated?\n\n"
        "## Per-Question Scoring\n"
        "For each question/answer pair in the transcript, evaluate the candidate's response "
        "on each dimension. Include the question text, answer text, scores, and brief feedback.\n\n"
        "## Output Format\n"
        "Return ONLY valid JSON with no markdown fences:\n"
        '{{"overall_score": <0.0-5.0>, '
        '"dimensions": {{"structure_star": {{"score": <0.0-5.0>, "evidence": "..."}}, '
        '"relevance": {{"score": <0.0-5.0>, "evidence": "..."}}, '
        '"specificity": {{"score": <0.0-5.0>, "evidence": "..."}}, '
        '"impact": {{"score": <0.0-5.0>, "evidence": "..."}}}}, '
        '"question_scores": [{{"question_index": 0, "question_text": "...", "answer_text": "...", '
        '"dimension_scores": {{"structure_star": {{"score": <0.0-5.0>, "evidence": "..."}}, '
        '"relevance": {{"score": <0.0-5.0>, "evidence": "..."}}, '
        '"specificity": {{"score": <0.0-5.0>, "evidence": "..."}}, '
        '"impact": {{"score": <0.0-5.0>, "evidence": "..."}}}}, '
        '"overall_score": <0.0-5.0>, "feedback": "..."}}], '
        '"strengths": ["..."], "improvements": ["..."], '
        '"recommendations": ["..."], "confidence": <0.0-1.0>}}'
    ),
}


class PromptRegistry:
    """Loads versioned evaluation prompts.

    Checks ``prompts/{type}/v{version}.md`` first, then falls back
    to built-in default templates.
    """

    def __init__(self) -> None:
        self._cache: dict[str, str] = {}

    def get_prompt(self, interview_type: str, version: str = "v1") -> str:
        """Return the prompt template for the given type and version."""
        cache_key = f"{interview_type}:{version}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        path = PROMPT_DIR / interview_type / f"{version}.md"
        if path.exists():
            template = path.read_text(encoding="utf-8")
        else:
            template = DEFAULT_EVALUATOR_PROMPTS.get(interview_type, DEFAULT_EVALUATOR_PROMPTS["behavioral"])

        self._cache[cache_key] = template
        return template

    def build_prompt(
        self,
        interview_type: str,
        company: str,
        role: str,
        experience_level: str,
        transcript: str,
        language: str = "",
        code_submission: str = "",
        test_results: str = "",
        version: str = "v1",
    ) -> str:
        """Interpolate context into the evaluation prompt template."""
        template = self.get_prompt(interview_type, version)
        return template.format(
            company=company,
            role=role,
            level=experience_level,
            language=language or "N/A",
            transcript=transcript or "No transcript available.",
            code_submission=code_submission or "No code submitted.",
            test_results=test_results or "No test results.",
        )
