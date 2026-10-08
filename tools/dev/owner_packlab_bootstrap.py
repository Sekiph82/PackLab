"""Start PackLab Studio from the isolated OWNER DEV runtime."""

from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path


def main() -> None:
    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        raise RuntimeError("LOCALAPPDATA is not available")
    runtime_root = Path(local_app_data) / "PackLab" / "OwnerDev" / "current"
    required = (
        runtime_root / "owner-dev-runtime.json",
        runtime_root / "apps" / "windows-studio" / "src",
        runtime_root / "core" / "src",
    )
    if any(not path.exists() for path in required):
        raise RuntimeError("OWNER DEV runtime is incomplete")
    sys.path[:0] = [str(required[2]), str(required[1])]
    runpy.run_module("packlab_studio", run_name="__main__")


if __name__ == "__main__":
    main()
