import logging
from contextvars import ContextVar

request_id: ContextVar[str] = ContextVar("request_id", default="")


class _RequestIDFormatter(logging.Formatter):
    """Injects ``request_id`` into every record, defaulting to ``""`` when
    the ContextVar hasn't been set (e.g. startup / background tasks)."""

    def format(self, record: logging.LogRecord) -> str:
        record.request_id = request_id.get()
        return super().format(record)


def setup_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(_RequestIDFormatter("%(asctime)s | %(levelname)s | request_id=%(request_id)s | %(message)s"))
    root = logging.getLogger()
    # Remove pre-existing handlers (from uvicorn etc.) to avoid duplicates
    for h in root.handlers[:]:
        root.removeHandler(h)
    root.addHandler(handler)
    root.setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
