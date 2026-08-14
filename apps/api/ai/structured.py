"""Structured output helpers.

Extracts well-formed JSON from LLM responses that may be wrapped in
markdown code fences or padded with explanatory prose.
"""

from __future__ import annotations

import json
import re

_FENCE_RE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL)


def extract_json_content(content: str) -> str:
    """Strip markdown fences and surrounding prose, returning the JSON substring."""
    stripped = content.strip()

    match = _FENCE_RE.match(stripped)
    if match:
        return match.group(1).strip()

    start = stripped.find("{")
    end = stripped.rfind("}")
    if start != -1 and end > start:
        return stripped[start : end + 1]

    start = stripped.find("[")
    end = stripped.rfind("]")
    if start != -1 and end > start:
        return stripped[start : end + 1]

    return stripped


def parse_json_response(response_model: type, content: str) -> dict | list:
    """Parse an LLM response into a JSON dict, tolerating fences/prose.

    ``response_model`` is currently a compatibility parameter; callers may
    provide a Pydantic model to validate against in a later phase.  Raises
    ``json.JSONDecodeError`` on unparseable input (same contract as the
    previous inline parser).
    """
    if isinstance(content, (dict, list)):
        return content

    raw = extract_json_content(content)
    data = json.loads(raw)
    if response_model is not None and hasattr(response_model, "model_validate"):
        return response_model.model_validate(data)
    return data
