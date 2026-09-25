"""Versioned, portable and atomic Studio UI preferences."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

PREFERENCES_SCHEMA_VERSION = 1
DEFAULT_GEOMETRY = (80, 80, 1280, 800)


@dataclass(frozen=True, slots=True)
class WindowPreferences:
    schema_version: int = PREFERENCES_SCHEMA_VERSION
    geometry: tuple[int, int, int, int] = DEFAULT_GEOMETRY
    maximized: bool = False
    fullscreen: bool = False
    dock_state: str = ""
    last_route: str = "library"
    theme: str = "system"
    display_scale: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["geometry"] = list(self.geometry)
        return value


def sanitize_geometry(value: Any, *, bounds: tuple[int, int, int, int] | None = None) -> tuple[int, int, int, int]:
    """Return safe geometry, clamped to the available desktop when supplied."""

    if not isinstance(value, (list, tuple)) or len(value) != 4:
        return DEFAULT_GEOMETRY
    try:
        x, y, width, height = (int(item) for item in value)
    except (TypeError, ValueError):
        return DEFAULT_GEOMETRY
    width = max(640, min(width, 10000))
    height = max(480, min(height, 10000))
    if bounds is not None:
        bx, by, bw, bh = bounds
        x = min(max(x, bx), bx + max(0, bw - 80))
        y = min(max(y, by), by + max(0, bh - 80))
    return x, y, width, height


class PreferencesStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load(self) -> WindowPreferences:
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
        except (FileNotFoundError, OSError, ValueError, TypeError):
            return WindowPreferences()
        if not isinstance(value, dict):
            return WindowPreferences()
        migrated = self._migrate(value)
        if migrated is None:
            return WindowPreferences()
        return WindowPreferences(
            geometry=sanitize_geometry(migrated.get("geometry")),
            maximized=bool(migrated.get("maximized", False)),
            fullscreen=bool(migrated.get("fullscreen", False)),
            dock_state=str(migrated.get("dock_state", "")) if isinstance(migrated.get("dock_state", ""), str) else "",
            last_route=str(migrated.get("last_route", "library")),
            theme=str(migrated.get("theme", "system")),
            display_scale=float(migrated.get("display_scale", 1.0)),
        )

    def save(self, preferences: WindowPreferences) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary_name = tempfile.mkstemp(prefix=f".{self.path.name}-", suffix=".tmp", dir=self.path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                json.dump(preferences.to_dict(), handle, sort_keys=True, separators=(",", ":"))
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_name, self.path)
        finally:
            Path(temporary_name).unlink(missing_ok=True)

    def reset(self) -> WindowPreferences:
        defaults = WindowPreferences()
        self.save(defaults)
        return defaults

    @staticmethod
    def _migrate(value: dict[str, Any]) -> dict[str, Any] | None:
        version = value.get("schema_version", 0)
        if version == PREFERENCES_SCHEMA_VERSION:
            return value
        if version == 0:
            migrated = dict(value)
            migrated["schema_version"] = PREFERENCES_SCHEMA_VERSION
            migrated["last_route"] = migrated.pop("last_page", "library")
            return migrated
        return None
