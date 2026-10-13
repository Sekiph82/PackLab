"""Cheap, native-build-free smoke for the OCCT SDK producer/consumer layout contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

from tools.packaging.audit_controlled_occt_sdk_dependencies import sdk_dependency_deficiencies
from tools.packaging.build_controlled_occt_sdk import (
    CONTRACT,
    LOCK,
    OCCT_CMAKE_OPTIONS,
    OCCT_ID,
    PARALLELISM,
    SDK_VERSION,
    validate_installed_sdk,
)
from tools.packaging.validate_controlled_occt_sdk import METADATA_NAME, validate_sdk
from tools.packaging.validate_windows_native_source_lock import load_source_lock

RUN_ID = "layout-fixture"
ATTEMPT = "1"
CACHE_KEY = "fixture-v4"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def create_fixture(root: Path) -> dict[str, Any]:
    payloads = {
        "inc/OpenGl_Context.hxx": b"fixture OpenGl_Context header\n",
        "win64/vc14/lib/TKOpenGl.lib": b"fixture import library\n",
        "win64/vc14/bin/TKOpenGl.dll": b"fixture runtime dll\n",
        "win64/vc14/lib/TKernel.lib": b"fixture base import library\n",
        "win64/vc14/bin/TKernel.dll": b"fixture base runtime dll\n",
        "cmake/OpenCASCADEConfig.cmake": (
            b'set (OpenCASCADE_INSTALL_PREFIX "${CMAKE_CURRENT_LIST_DIR}/..")\n'
            b'set (OpenCASCADE_BINARY_DIR "${OpenCASCADE_INSTALL_PREFIX}/win64/vc14/bin")\n'
            b'set (OpenCASCADE_LIBRARY_DIR "${OpenCASCADE_INSTALL_PREFIX}/win64/vc14/lib")\n'
            b'set (OpenCASCADE_INCLUDE_DIR "${OpenCASCADE_INSTALL_PREFIX}/inc")\n'
            b"set (OpenCASCADE_LIBRARIES TKOpenGl TKernel)\n"
        ),
        "cmake/OpenCASCADEVisualizationTargets.cmake": (
            b"set_target_properties(TKOpenGl PROPERTIES\n"
            b'  IMPORTED_IMPLIB_RELEASE "${_IMPORT_PREFIX}/win64/vc14/lib/TKOpenGl.lib"\n'
            b'  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/win64/vc14/bin/TKOpenGl.dll")\n'
        ),
    }
    entries: list[dict[str, Any]] = []
    for relative, payload in payloads.items():
        path = root / Path(relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        entries.append(
            {
                "relative_path": relative,
                "byte_length": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        )
    layout = validate_installed_sdk(root)
    record = next(row for row in load_source_lock(LOCK)["records"] if row["id"] == OCCT_ID)
    payload = json.dumps(entries, sort_keys=True, separators=(",", ":")).encode()
    metadata = {
        "schema_version": 2,
        "status": "SEALED",
        "stage": "occt-sdk",
        "producer_job_id": "occt-sdk",
        "producer_run_id": RUN_ID,
        "producer_run_attempt": ATTEMPT,
        "cache_key": CACHE_KEY,
        "source_lock_sha256": digest(LOCK),
        "toolchain_contract_sha256": digest(CONTRACT),
        "occt_source_id": OCCT_ID,
        "occt_source_revision": record["revision"],
        "occt_source_sha256": record["sha256"],
        "windows_sdk": SDK_VERSION,
        "python": "3.12.15",
        "cmake": "cmake version 3.31.8",
        "compiler": "MSVC 19.44.35229.0",
        "parallelism": PARALLELISM,
        "cmake_options": OCCT_CMAKE_OPTIONS,
        "sdk_layout": layout,
        "file_count": len(entries),
        "byte_count": sum(entry["byte_length"] for entry in entries),
        "files": entries,
        "payload_sha256": hashlib.sha256(payload).hexdigest(),
    }
    (root / METADATA_NAME).write_text(json.dumps(metadata), encoding="utf-8")
    return metadata


def run_smoke() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="packlab-occt-layout-") as temporary:
        root = Path(temporary) / "nested-sdk"
        root.mkdir()
        metadata = create_fixture(root)
        validate_sdk(root, RUN_ID, ATTEMPT, CACHE_KEY, require_opengl=True)
        files = {item["relative_path"] for item in metadata["files"]}
        missing_libraries, missing_runtimes = sdk_dependency_deficiencies({}, {"TKOpenGl"}, files)
        if missing_libraries or missing_runtimes:
            raise ValueError("dependency scanner rejected the canonical TKOpenGl fixture")

        flattened = Path(temporary) / "flattened-only-sdk"
        shutil.copytree(root, flattened)
        for path in (
            flattened / "win64/vc14/lib/TKOpenGl.lib",
            flattened / "win64/vc14/bin/TKOpenGl.dll",
        ):
            path.unlink()
        (flattened / "lib").mkdir()
        (flattened / "bin").mkdir()
        shutil.copy2(root / "win64/vc14/lib/TKOpenGl.lib", flattened / "lib/TKOpenGl.lib")
        shutil.copy2(root / "win64/vc14/bin/TKOpenGl.dll", flattened / "bin/TKOpenGl.dll")
        try:
            validate_installed_sdk(flattened)
        except ValueError:
            pass
        else:
            raise ValueError("producer post-install seam accepted a flattened-only SDK")
        return {
            "status": "PASS",
            "producer_post_install": "PASS",
            "consumer_validator": "PASS",
            "downstream_dependency_scanner": "PASS",
            "canonical_paths": metadata["sdk_layout"]["required_files"],
            "native_build_invoked": False,
        }


def main() -> int:
    argparse.ArgumentParser(description=__doc__).parse_args()
    result = run_smoke()
    print("OCCT_SDK_LAYOUT_PREFLIGHT " + json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
