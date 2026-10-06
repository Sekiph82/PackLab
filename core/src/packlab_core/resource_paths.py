"""PackLab-owned read-only resources for source and frozen applications."""

from __future__ import annotations

import sys
from pathlib import Path


def packlab_data_root() -> Path:
    """Return the packaged resource root or repository root in a source checkout."""

    frozen_root = getattr(sys, "_MEIPASS", None)
    if isinstance(frozen_root, str) and frozen_root:
        return Path(frozen_root)
    return Path(__file__).resolve().parents[3]
