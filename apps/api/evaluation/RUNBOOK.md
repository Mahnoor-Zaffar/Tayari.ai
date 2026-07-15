# AI Evaluation Engine — Operational Runbook

## Architecture

```
Interview Complete
    │
    ▼
POST /api/v1/evaluations/{interview_id}
    │
    ▼
EvaluationPipeline.evaluate()
    ├── 1. Collect transcript + metadata
    ├── 2. Sanitize content (PII redaction, injection prevention)
    ├── 3. Build type-specific prompt
    ├── 4. Call AI provider (up to 3 retries)
    ├── 5. Validate structured output
    └── 6. Return EvaluationResult (never raw AI output)
    │
    ▼
EvaluationRepository.create_evaluation()
    └── Persist validated result to DB
    │
    ▼
Client (frontend dashboard)
```

## Key Principles

| Principle | Enforcement |
|---|---|
| **LLM never writes to DB** | `ResultValidator` validates all AI output before any write |
| **All user content sanitized** | `sanitize.py` redacts PII, strips control chars, truncates |
| **Retry with backoff** | Up to 3 attempts, logs each failure |
| **Graceful degradation** | Returns `status: "failed"` with 0.0 scores on exhaustion |

## Prompt Registry

Prompts are loaded from `evaluation/prompts/{type}/{version}.md`. If no file exists, fallback defaults in `prompt_registry.py` are used. Prompts are cached in memory after first load.

### Prompt Versions

| Type | Default Version | File |
|---|---|---|
| Coding | `v1` | `evaluation/prompts/coding/v1.md` |
| System Design | `v1` | `evaluation/prompts/system-design/v1.md` |
| Behavioral | `v1` | `evaluation/prompts/behavioral/v1.md` |

### Adding a New Prompt Version

1. Create `evaluation/prompts/{type}/v2.md`
2. Pass `prompt_version="v2"` to `EvaluationPipeline.evaluate()`

## API Endpoints

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/v1/evaluations/{interview_id}` | Trigger evaluation pipeline |
| `GET` | `/api/v1/evaluations/{interview_id}` | Get evaluation result |

## Monitoring

### Key Metrics

| Metric | Source | Alert |
|---|---|---|
| `evaluation_latency_ms` | Pipeline timing | > 15s |
| `evaluation_failures` | Pipeline fallback count | > 5% of evaluations |
| `evaluation_retries` | Per-evaluation retry count | > 2 |
| `pii_redactions` | Sanitizer matches | Logged per evaluation |

### Logged Events

```
event=evaluation.started   interview_id=abc123 type=coding
event=evaluation.retry     interview_id=abc123 attempt=2 error="Validation failed"
event=evaluation.completed interview_id=abc123 score=4.2 status=completed latency_ms=8400
event=evaluation.failed    interview_id=abc123 error="All retries exhausted" status=failed
```

## Debugging

```bash
# Trigger evaluation manually
curl -X POST http://localhost:8000/api/v1/evaluations/{interview_id} \
  -H "Authorization: Bearer $TOKEN"

# Check evaluation result
curl -s http://localhost:8000/api/v1/evaluations/{interview_id} \
  -H "Authorization: Bearer $TOKEN" | jq .

# Validate prompt locally (examine what would be sent)
python3 -c "
from evaluation.prompt_registry import PromptRegistry
print(PromptRegistry().get_prompt('coding'))
"
```
