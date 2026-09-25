"""Versioned PackLab project layout and safe path authority."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

LAYOUT_SCHEMA_VERSION = "1.0"
_DIRECTORIES = ("raw", "working", "derived", "cache", "temp", "export", "history", "recovery")


class ProjectLayoutError(ValueError):
    pass


def safe_relative_path(value: str | Path) -> Path:
    path = Path(value)
    text = str(value).replace("/", "\\")
    if path.is_absolute() or (len(text) >= 2 and text[1] == ":"):
        raise ProjectLayoutError("absolute project-relative path is forbidden")
    parts = path.parts
    if not parts or any(part in {"", ".", ".."} for part in parts):
        raise ProjectLayoutError("path traversal or empty component is forbidden")
    return path


@dataclass(frozen=True, slots=True)
class ProjectLayout:
    root: Path

    @property
    def marker_path(self) -> Path:
        return self.root / ".packlab-layout.json"

    @classmethod
    def create(cls, root: str | Path) -> ProjectLayout:
        target = Path(root)
        if target.exists() and any(target.iterdir()):
            raise ProjectLayoutError("project destination already exists and is not empty")
        target.mkdir(parents=True, exist_ok=True)
        for directory in _DIRECTORIES:
            (target / directory).mkdir()
        marker = {"format": "packlab-project-layout", "schema_version": LAYOUT_SCHEMA_VERSION, "directories": list(_DIRECTORIES)}
        cls._atomic_json(target / ".packlab-layout.json", marker)
        return cls(target)

    @classmethod
    def open(cls, root: str | Path) -> ProjectLayout:
        layout = cls(Path(root))
        layout.validate()
        return layout

    def validate(self) -> None:
        try:
            value = json.loads(self.marker_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, OSError, ValueError) as error:
            raise ProjectLayoutError("project layout marker is missing or corrupt") from error
        if value.get("schema_version") != LAYOUT_SCHEMA_VERSION or tuple(value.get("directories", ())) != _DIRECTORIES:
            raise ProjectLayoutError("unsupported project layout schema")
        missing = [directory for directory in _DIRECTORIES if not (self.root / directory).is_dir()]
        if missing:
            raise ProjectLayoutError(f"project layout directories missing: {','.join(missing)}")

    def path(self, area: str, relative: str | Path = "") -> Path:
        if area not in _DIRECTORIES:
            raise ProjectLayoutError(f"unknown project area: {area}")
        if relative == "":
            return self.root / area
        safe = safe_relative_path(relative)
        candidate = (self.root / area / safe).resolve(strict=False)
        area_root = (self.root / area).resolve()
        if os.path.commonpath((str(area_root), str(candidate))) != str(area_root):
            raise ProjectLayoutError("project path escapes its area")
        return candidate

    @staticmethod
    def _atomic_json(target: Path, value: object) -> None:
        fd, temporary_name = tempfile.mkstemp(prefix=f".{target.name}-", suffix=".tmp", dir=target.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                json.dump(value, handle, sort_keys=True, separators=(",", ":"))
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_name, target)
        finally:
            Path(temporary_name).unlink(missing_ok=True)

