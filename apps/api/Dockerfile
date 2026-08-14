FROM python:3.13-slim

WORKDIR /app

RUN pip install uv --quiet

COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --quiet

# Embedded Redis (same container) so the app runs without a separate Redis
# service. Used for the JWT blacklist + shared rate limiting. Persistence is
# disabled on purpose — the data is ephemeral and reconstructible.
RUN apt-get update && apt-get install -y --no-install-recommends redis-server \
    && rm -rf /var/lib/apt/lists/*

COPY . .

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["sh", "-c", "redis-server --bind 127.0.0.1 --port 6379 --save '' --appendonly no & exec uv run uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
