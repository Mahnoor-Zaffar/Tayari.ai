import logging
from contextvars import ContextVar

request_id: ContextVar[str] = ContextVar("request_id", default="")


def setup_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)s | request_id=%(request_id)s | %(message)s"
    ))
    root = logging.getLogger()
    root.addHandler(handler)
    root.setLevel(logging.INFO)


def get_logger(name: str) -> logging.LoggerAdapter:
    base = logging.getLogger(name)
    return logging.LoggerAdapter(base, {"request_id": request_id.get()})
