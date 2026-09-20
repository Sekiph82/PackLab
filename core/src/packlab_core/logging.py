"""Opt-in structured logging with safe correlation and redaction defaults."""

from __future__ import annotations

import contextvars
import json
import logging
import re
import sys
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from typing import Any, TextIO

REDACTED = "<REDACTED>"
_CORRELATION: contextvars.ContextVar[dict[str, str | None]] = contextvars.ContextVar(
    "packlab_logging_correlation", default={}
)
_SENSITIVE_KEYS = {"password", "secret", "token", "authorization", "credential", "api_key"}
_PRIVATE_PATH = re.compile(r"(?i)(?:[a-z]:\\users\\[^\s]+|/(?:users|home)/[^\s]+)")


def _safe_value(value: Any, key: str | None = None) -> Any:
    if key and (
        key.lower() in _SENSITIVE_KEYS or any(word in key.lower() for word in _SENSITIVE_KEYS)
    ):
        return REDACTED
    if isinstance(value, Mapping):
        return {
            str(item_key): _safe_value(item_value, str(item_key))
            for item_key, item_value in value.items()
        }
    if isinstance(value, (list, tuple, set)):
        return [_safe_value(item) for item in value]
    if isinstance(value, str):
        return _PRIVATE_PATH.sub(REDACTED, value)
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return str(value)


def _correlation() -> dict[str, str | None]:
    current = _CORRELATION.get()
    return {key: current.get(key) for key in ("session_id", "task_id", "job_id")}


@contextmanager
def correlation_context(
    *, session_id: str | None = None, task_id: str | None = None, job_id: str | None = None
) -> Iterator[None]:
    """Temporarily add correlation values without requiring a PL task identifier."""

    current = _correlation()
    values = {
        key: value if value is not None else current.get(key)
        for key, value in {"session_id": session_id, "task_id": task_id, "job_id": job_id}.items()
    }
    token = _CORRELATION.set(values)
    try:
        yield
    finally:
        _CORRELATION.reset(token)


class SafeJsonFormatter(logging.Formatter):
    """Format stable event fields as one redacted JSON object per record."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "event": getattr(record, "event", "log"),
            "message": record.getMessage(),
            **_correlation(),
            "fields": getattr(record, "fields", {}),
        }
        return json.dumps(_safe_value(payload), sort_keys=True, separators=(",", ":"))


class SafeHumanFormatter(logging.Formatter):
    """Format the same safe message for a human terminal."""

    def format(self, record: logging.LogRecord) -> str:
        correlation = ", ".join(
            f"{key}={value}" for key, value in _correlation().items() if value is not None
        )
        suffix = f" [{correlation}]" if correlation else ""
        return f"{record.levelname} {getattr(record, 'event', 'log')}{suffix}: {_safe_value(record.getMessage())}"


class CorrelationFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        for key, value in _correlation().items():
            setattr(record, key, value)
        record.fields = _safe_value(getattr(record, "fields", {}))
        return True


def configure_logger(
    name: str = "packlab",
    *,
    stream: TextIO | None = None,
    structured: bool = True,
    level: int = logging.INFO,
) -> logging.Logger:
    """Create/configure one named logger; importing this module changes no global handlers."""

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False
    handler = logging.StreamHandler(stream or sys.stderr)
    handler.addFilter(CorrelationFilter())
    handler.setFormatter(SafeJsonFormatter() if structured else SafeHumanFormatter())
    logger.handlers.clear()
    logger.addHandler(handler)
    return logger


def log_event(logger: logging.Logger, level: int, event: str, message: str, **fields: Any) -> None:
    """Emit one safe event with optional structured fields."""

    logger.log(level, _safe_value(message), extra={"event": event, "fields": _safe_value(fields)})
