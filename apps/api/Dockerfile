FROM python:3.13-slim

WORKDIR /app

RUN pip install uv --quiet

# Build context is the repo root so packages/prompts can be copied in.
COPY apps/api/pyproject.toml apps/api/uv.lock ./
RUN uv sync --no-dev --quiet

# Embedded Redis (same container) so the app runs without a separate Redis
# service. Used for the JWT blacklist + shared rate limiting. Persistence is
# disabled on purpose — the data is ephemeral and reconstructible.
RUN apt-get update && apt-get install -y --no-install-recommends redis-server \
    && rm -rf /var/lib/apt/lists/*

COPY apps/api/ .
# Prompt templates live in the packages workspace. Bake the evaluator prompts
# (packages/prompts is the source of truth) into the layout PromptRegistry
# reads: evaluation/prompts/{type}/v{version}.md.
COPY packages/prompts /packages/prompts
RUN mkdir -p /app/evaluation/prompts && \
    for t in behavioral system-design coding; do \
      if [ -f "/packages/prompts/evaluators/$t.md" ]; then \
        mkdir -p "/app/evaluation/prompts/$t" && \
        cp "/packages/prompts/evaluators/$t.md" "/app/evaluation/prompts/$t/v1.md"; \
      fi; \
    done

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["sh", "-c", "redis-server --bind 127.0.0.1 --port 6379 --save '' --appendonly no & exec uv run uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
