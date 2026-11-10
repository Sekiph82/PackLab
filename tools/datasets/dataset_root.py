"""Pre-resolution checks for PackLab's dedicated external dataset root."""

from __future__ import annotations

import os
import re
from pathlib import Path


def is_reparse_point(path: Path) -> bool:
    return path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction())


def resolve_dataset_root(requested: Path, localappdata: Path) -> Path:
    """Require the canonical M17 path and reject linked suffixes before resolve."""
    requested_spelling = str(requested.expanduser())
    if any(part in {".", ".."} for part in re.split(r"[\\/]+", requested_spelling)):
        raise ValueError("dataset root path may not contain dot segments")
    expected = Path(os.path.abspath(localappdata / "PackLab" / "datasets" / "M17"))
    requested_absolute = Path(os.path.abspath(requested_spelling))
    if os.path.normcase(str(requested_absolute)) != os.path.normcase(str(expected)):
        raise ValueError("dataset root must be the dedicated %LOCALAPPDATA%/PackLab/datasets/M17 directory")

    # The host may redirect LocalAppData itself; check only PackLab-owned suffixes.
    current = Path(os.path.abspath(localappdata))
    for component in ("PackLab", "datasets", "M17"):
        current = current / component
        if is_reparse_point(current):
            raise ValueError(f"dataset root traverses a symlink or junction: {current}")

    resolved = requested_absolute.resolve(strict=True)
    resolved_expected = expected.resolve(strict=True)
    if resolved != resolved_expected or (resolved / ".git").exists():
        raise ValueError("dataset root must resolve to the dedicated outside-Git M17 directory")
    return resolved
