"""Versioned PackLab project layout and safe path authority."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath

LAYOUT_SCHEMA_VERSION = "1.0"
_DIRECTORIES = ("raw", "working", "derived", "cache", "temp", "export", "history", "recovery")


class ProjectLayoutError(ValueError):
    pass


_RESERVED_DEVICE_NAMES = frozenset(
    {"CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$"}
    | {f"{name}{suffix}" for name in ("COM", "LPT") for suffix in (*"123456789", "¹", "²", "³")}
)


def safe_relative_path(value: str | Path) -> Path:
    """A project-relative path that cannot name anything outside its base on Windows or POSIX.

    Rejects drives, roots ("/x", "\\x"), UNC and device prefixes ("\\\\server", "\\\\?\\",
    "\\\\.\\"), ':' anywhere (drive-relative "C:x" and NTFS streams "a:b"), "."/".." and
    components Windows silently rewrites: trailing dot or space and reserved device names.
    """

    text = str(value)
    if not text or text.startswith(("/", "\\")) or ":" in text:
        raise ProjectLayoutError("absolute, rooted, drive or stream path is forbidden")
    windows, posix = PureWindowsPath(text), PurePosixPath(text)
    if windows.drive or windows.root or windows.anchor or posix.root or posix.anchor:
        raise ProjectLayoutError("absolute, rooted, drive or stream path is forbidden")
    # Split on both separators; dropping "" and "." matches what Path did ("a//./b" == "a/b").
    parts = [part for part in text.replace("\\", "/").split("/") if part not in {"", "."}]
    if not parts:
        raise ProjectLayoutError("path traversal or empty component is forbidden")
    for part in parts:
        if part == ".." or part != part.rstrip(". "):
            raise ProjectLayoutError("path traversal, empty or trailing dot/space component")
        if part.split(".")[0].rstrip(" ").upper() in _RESERVED_DEVICE_NAMES:
            raise ProjectLayoutError("reserved Windows device name is forbidden")
    return Path(*parts)


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
        marker = {
            "format": "packlab-project-layout",
            "schema_version": LAYOUT_SCHEMA_VERSION,
            "directories": list(_DIRECTORIES),
        }
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
        if (
            value.get("schema_version") != LAYOUT_SCHEMA_VERSION
            or tuple(value.get("directories", ())) != _DIRECTORIES
        ):
            raise ProjectLayoutError("unsupported project layout schema")
        missing = [directory for directory in _DIRECTORIES if not (self.root / directory).is_dir()]
        if missing:
            raise ProjectLayoutError(f"project layout directories missing: {','.join(missing)}")

    def path(self, area: str, relative: str | Path = "") -> Path:
        if area not in _DIRECTORIES:
            raise ProjectLayoutError(f"unknown project area: {area}")
        if relative == "":
            return self.root / area
        # Lexical containment: safe_relative_path already rejects absolute and ".." parts, so
        # root/area/safe cannot leave the area by name. Path.resolve() is deliberately not used:
        # redirected AppData (MSIX), OneDrive and junctions above the project resolve the file
        # and the area into different trees and made valid projects unopenable (F2).
        safe = safe_relative_path(relative)
        area_root = Path(os.path.abspath(self.root / area))  # absolute, links not followed
        candidate = area_root / safe
        area_text = os.path.normcase(os.path.normpath(area_root))
        candidate_text = os.path.normcase(os.path.normpath(candidate))
        if os.path.commonpath((area_text, candidate_text)) != area_text:  # defence in depth
            raise ProjectLayoutError("project path escapes its area")
        # The only remaining escape is a link at or inside the area; reject existing ones.
        current = area_root
        for step in (None, *safe.parts):
            current = current if step is None else current / step
            if current.is_symlink() or current.is_junction():
                raise ProjectLayoutError("project path escapes its area through a link")
        return candidate

    @staticmethod
    def _atomic_json(target: Path, value: object) -> None:
        fd, temporary_name = tempfile.mkstemp(
            prefix=f".{target.name}-", suffix=".tmp", dir=target.parent
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                json.dump(value, handle, sort_keys=True, separators=(",", ":"))
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_name, target)
        finally:
            Path(temporary_name).unlink(missing_ok=True)
