"""Explicit local, bounded and privacy-safe diagnostic bundle creation."""

from __future__ import annotations

import json
import os
import platform
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_SECRET = re.compile(r"(?i)\b(bearer|token|password|passwd|api[_-]?key|pairing[_-]?code|private[_-]?key)\b(?:\s*[:=]\s*|\s+)([^,\s]+)")
_SECRET_FIELD = re.compile(r"(?i)(bearer|token|password|passwd|api[_-]?key|pairing[_-]?code|private[_-]?key)")
_WINDOWS_PATH = re.compile(r"(?i)([a-z]:\\[^\s\"']+|\\\\[^\s\"']+)")
MAX_LOG_BYTES = 32_000
MAX_ERROR_COUNT = 100


def redact(value: str) -> str:
    value = _SECRET.sub(lambda match: f"{match.group(1)}: [REDACTED]", value)
    return _WINDOWS_PATH.sub("[PATH_REDACTED]", value)


@dataclass(frozen=True, slots=True)
class DiagnosticBundle:
    path: Path
    bytes_written: int


class DiagnosticsBundleService:
    def __init__(self, diagnostics_root: str | Path, *, max_log_bytes: int = MAX_LOG_BYTES) -> None:
        self.diagnostics_root = Path(diagnostics_root)
        self.max_log_bytes = max(1024, max_log_bytes)

    def create_bundle(
        self,
        destination: str | Path | None = None,
        *,
        logs: str = "",
        build_info: dict[str, Any] | None = None,
        active_jobs: list[dict[str, Any]] | None = None,
        structured_errors: list[dict[str, Any]] | None = None,
    ) -> DiagnosticBundle:
        target = Path(destination) if destination is not None else self.diagnostics_root / "packlab-diagnostic.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "format": "packlab-diagnostic-bundle-v1",
            "build": self._safe_mapping(build_info or {}),
            "runtime": {"os": platform.platform(), "python": platform.python_version()},
            "logs": redact(logs)[: self.max_log_bytes],
            "active_jobs": self._safe_list(active_jobs or []),
            "structured_errors": self._safe_list(structured_errors or [])[-MAX_ERROR_COUNT:],
        }
        data = (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
        fd, temporary_name = tempfile.mkstemp(prefix=f".{target.name}-", suffix=".tmp", dir=target.parent)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_name, target)
        finally:
            Path(temporary_name).unlink(missing_ok=True)
        return DiagnosticBundle(target, len(data))

    @staticmethod
    def _safe_mapping(value: dict[str, Any]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key)
            result[redact(key_text)] = "[REDACTED]" if _SECRET_FIELD.search(key_text) else redact(str(item))
        return result

    @staticmethod
    def _safe_list(values: list[dict[str, Any]]) -> list[dict[str, str]]:
        return [
            {
                redact(str(key)): "[REDACTED]" if _SECRET_FIELD.search(str(key)) else redact(str(item))
                for key, item in value.items()
            }
            for value in values
        ]
