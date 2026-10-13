"""Fail-closed parity check for the OCCT SDK cache and producer inputs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from tools.packaging.build_controlled_occt_sdk import (
    CONTRACT as RUNTIME_CONTRACT,
)
from tools.packaging.build_controlled_occt_sdk import (
    GENERATOR,
    LOCK,
    OCCT_CMAKE_OPTIONS,
    OCCT_ID,
    PARALLELISM,
    SDK_VERSION,
)
from tools.packaging.validate_windows_native_source_lock import load_source_lock

SDK_CONTRACT = Path("tools/packaging/windows_occt_sdk_build_contract.json")
EXPECTED_CACHE_INPUTS = [
    "tools/packaging/windows_native_source_lock.json",
    "tools/packaging/packlab-ocp-bindings-win.lock",
    "tools/packaging/windows_occt_sdk_build_contract.json",
    "tools/packaging/build_controlled_occt_sdk.py",
    "tools/packaging/validate_controlled_occt_sdk.py",
    "tools/packaging/windows_occt_sdk_layout.py",
    "tools/packaging/audit_controlled_occt_sdk_dependencies.py",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_contract(path: Path = SDK_CONTRACT) -> dict[str, Any]:
    contract = json.loads(path.read_text(encoding="utf-8"))
    native_lock = load_source_lock(LOCK)
    runtime = json.loads(RUNTIME_CONTRACT.read_text(encoding="utf-8"))
    source = next(row for row in native_lock["records"] if row["id"] == OCCT_ID)
    locked_build = native_lock["build_environment_lock"]
    expected = {
        "schema_version": 1,
        "target": {
            "operating_system": "Windows",
            "runner_image": runtime["target"]["runner_image"],
            "architecture": "x86_64",
            "python": runtime["target"]["python_version"],
        },
        "occt_source": {
            "record_id": OCCT_ID,
            "version": source["version"],
            "revision": source["revision"],
            "sha256": source["sha256"],
        },
        "build_environment_lock": {
            "path": locked_build["path"],
            "sha256": locked_build["sha256"],
            "platform": locked_build["platform"],
        },
        "cmake": runtime["toolchain"]["cmake"],
        "compiler": runtime["toolchain"]["compiler"],
        "windows_sdk": SDK_VERSION,
        "generator": GENERATOR,
        "parallelism": PARALLELISM,
        "cmake_options": OCCT_CMAKE_OPTIONS,
        "cache_identity_files": EXPECTED_CACHE_INPUTS,
    }
    if contract != expected:
        raise ValueError(
            "OCCT SDK cache/build contract differs from producer, source, or toolchain"
        )
    if (
        runtime["windows_sdk_version"] != SDK_VERSION
        or runtime["cmake_generator"] != GENERATOR
        or runtime["cmake_parallel"] != PARALLELISM
    ):
        raise ValueError(
            "OCCT SDK build contract conflicts with the shared Windows runtime contract"
        )
    return contract


def main() -> int:
    validate_contract()
    print(f"WINDOWS_OCCT_SDK_BUILD_CONTRACT_PASS sha256={sha256(SDK_CONTRACT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
