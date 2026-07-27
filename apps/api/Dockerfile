FROM python:3.13-slim

WORKDIR /app

RUN pip install uv --quiet

COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --quiet

COPY . .

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
