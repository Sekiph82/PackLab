"""Headless Windows ingest boundary for drop and file-picker inputs."""

from __future__ import annotations

import hashlib
import os
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from packlab_core.packscan import PackScanError, PackScanReport, validate_packscan


@dataclass(frozen=True, slots=True)
class ImportResult:
    source_channel: str
    state: str
    source_name: str
    capture_id: str | None = None
    package_sha256: str | None = None
    error_code: str | None = None
    error_message: str | None = None


class FilePickerAdapter(Protocol):
    def choose_packscan(self) -> Path | None: ...


class DeterministicFilePicker:
    def __init__(self, selection: str | Path | None) -> None:
        self.selection = Path(selection) if selection is not None else None

    def choose_packscan(self) -> Path | None:
        return self.selection


class ImportService:
    """Single validation seam used by manual and network channels.

    Later stages add quarantine/raw/index/report stores around this seam; this
    initial boundary deliberately does not expose unvalidated bytes as import.
    """

    def __init__(self, validator=validate_packscan) -> None:
        self.validator = validator

    @staticmethod
    def normalize_path(value: str | Path) -> Path:
        return Path(os.path.abspath(os.path.normpath(os.fspath(value))))

    def import_path(self, value: str | Path, *, source_channel: str) -> ImportResult:
        source = self.normalize_path(value)
        if source.suffix.lower() != ".packscan":
            return ImportResult(source_channel, "rejected", source.name, error_code="unsupported_extension", error_message="only .packscan files are accepted")
        if source.is_dir():
            return ImportResult(source_channel, "rejected", source.name, error_code="directory_not_file", error_message="directories are not importable packages")
        if not source.exists():
            return ImportResult(source_channel, "rejected", source.name, error_code="missing_path", error_message="package path does not exist")
        try:
            report: PackScanReport = self.validator(source)
        except PackScanError as error:
            return ImportResult(source_channel, "rejected", source.name, error_code=error.code, error_message=error.code)
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        capture_id = report.manifest.get("capture_id")
        return ImportResult(source_channel, "validated", source.name, capture_id=capture_id if isinstance(capture_id, str) else None, package_sha256=digest)


class IngestController:
    def __init__(self, service: ImportService) -> None:
        self.service = service

    def ingest_dropped(self, paths: Sequence[str | Path]) -> list[ImportResult]:
        results: list[ImportResult] = []
        seen: set[str] = set()
        for value in paths:
            normalized = str(self.service.normalize_path(value)).casefold()
            if normalized in seen:
                source = self.service.normalize_path(value)
                results.append(ImportResult("drop", "rejected", source.name, error_code="duplicate_selection", error_message="the same package was selected more than once"))
                continue
            seen.add(normalized)
            results.append(self.service.import_path(value, source_channel="drop"))
        return results

    def ingest_from_picker(self, picker: FilePickerAdapter) -> ImportResult:
        selected = picker.choose_packscan()
        if selected is None:
            return ImportResult("picker", "cancelled", "", error_code="picker_cancelled", error_message="file picker was cancelled")
        return self.service.import_path(selected, source_channel="picker")
