"""Logging setup: one format, correlation id injected into every record."""
from __future__ import annotations

import contextvars
import logging

correlation_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("correlation_id", default="-")


class CorrelationIdFilter(logging.Filter):
    """Adds the current request's correlation id to each log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = correlation_id_var.get()
        return True


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler()
    handler.addFilter(CorrelationIdFilter())
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s [%(correlation_id)s] %(name)s: %(message)s")
    )
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())
    logging.getLogger("aiokafka").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
