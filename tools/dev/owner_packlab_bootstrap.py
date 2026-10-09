"""Start PackLab Studio from the isolated OWNER DEV runtime."""

from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path


def main() -> None:
    runtime_root = Path(__file__).resolve().parents[2]
    required = (
        runtime_root / "owner-dev-runtime.json",
        runtime_root / "apps" / "windows-studio" / "src",
        runtime_root / "core" / "src",
    )
    if any(not path.exists() for path in required):
        raise RuntimeError("OWNER DEV runtime is incomplete")
    import json

    manifest = json.loads(required[0].read_text(encoding="utf-8"))
    immutable_release = runtime_root.name == manifest.get("runtime_id")
    project_current = runtime_root.name == "current" and runtime_root.parent.name == "OwnerDev"
    if (
        manifest.get("source_commit") != os.environ.get("PACKLAB_OWNERDEV_SOURCE_SHA")
        or manifest.get("runtime_id") != os.environ.get("PACKLAB_OWNERDEV_RUNTIME_ID")
        or not (immutable_release or project_current)
    ):
        raise RuntimeError("OWNER DEV launcher/runtime identity mismatch")
    sys.path[:0] = [str(required[2]), str(required[1])]
    runpy.run_module("packlab_studio", run_name="__main__")


if __name__ == "__main__":
    main()
