from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pytest
from tools.packaging.build_controlled_occt_sdk import (
    CONTRACT,
    LOCK,
    OCCT_CMAKE_OPTIONS,
    OCCT_ID,
    SDK_VERSION,
    validate_installed_sdk,
)
from tools.packaging.preflight_occt_sdk_layout import run_smoke
from tools.packaging.validate_controlled_occt_sdk import METADATA_NAME, validate_sdk
from tools.packaging.validate_windows_native_source_lock import load_source_lock
from tools.packaging.windows_occt_sdk_layout import CANONICAL_OPENGL_FILES


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sealed_fixture(root: Path) -> None:
    payloads = {
        "inc/OpenGl_Context.hxx": b"header",
        "win64/vc14/lib/TKOpenGl.lib": b"import library",
        "win64/vc14/bin/TKOpenGl.dll": b"runtime",
        "win64/vc14/lib/TKernel.lib": b"base import library",
        "win64/vc14/bin/TKernel.dll": b"base runtime dll",
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
    entries = []
    for relative, payload in payloads.items():
        target = root / Path(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
        entries.append(
            {"relative_path": relative, "byte_length": len(payload), "sha256": _digest(payload)}
        )
    record = next(row for row in load_source_lock(LOCK)["records"] if row["id"] == OCCT_ID)
    layout = validate_installed_sdk(root)
    payload = json.dumps(entries, sort_keys=True, separators=(",", ":")).encode("utf-8")
    (root / METADATA_NAME).write_text(
        json.dumps(
            {
                "schema_version": 2,
                "status": "SEALED",
                "stage": "occt-sdk",
                "producer_job_id": "occt-sdk",
                "producer_run_id": "12345",
                "producer_run_attempt": "1",
                "cache_key": "sdk-key-v4",
                "payload_sha256": _digest(payload),
                "source_lock_sha256": _digest(LOCK.read_bytes()),
                "toolchain_contract_sha256": _digest(CONTRACT.read_bytes()),
                "occt_source_id": OCCT_ID,
                "occt_source_revision": record["revision"],
                "occt_source_sha256": record["sha256"],
                "windows_sdk": SDK_VERSION,
                "python": "3.12.15",
                "cmake": "cmake version 3.31.8",
                "compiler": "MSVC 19.44.35229.0",
                "parallelism": 4,
                "cmake_options": OCCT_CMAKE_OPTIONS,
                "sdk_layout": layout,
                "file_count": len(entries),
                "byte_count": sum(entry["byte_length"] for entry in entries),
                "files": entries,
            }
        ),
        encoding="utf-8",
    )


def test_sdk_checkpoint_validates_run_identity_and_every_file(tmp_path: Path) -> None:
    _sealed_fixture(tmp_path)
    result = validate_sdk(tmp_path, "12345", "1", "sdk-key-v4", require_opengl=True)
    assert result["file_count"] == 7
    assert result["sdk_layout"]["library_dir"] == "win64/vc14/lib"


def test_sdk_checkpoint_rejects_tampered_or_extra_files(tmp_path: Path) -> None:
    _sealed_fixture(tmp_path)
    (tmp_path / "win64/vc14/bin/TKOpenGl.dll").write_bytes(b"tampered")
    with pytest.raises(ValueError, match="hash/size"):
        validate_sdk(tmp_path, "12345", "1", "sdk-key-v4", require_opengl=True)
    (tmp_path / "win64/vc14/bin/TKOpenGl.dll").write_bytes(b"runtime")
    (tmp_path / "extra.dll").write_bytes(b"unlisted")
    with pytest.raises(ValueError, match="file set"):
        validate_sdk(tmp_path, "12345", "1", "sdk-key-v4", require_opengl=True)


def test_sdk_checkpoint_rejects_another_producer_run(tmp_path: Path) -> None:
    _sealed_fixture(tmp_path)
    with pytest.raises(ValueError, match="identity"):
        validate_sdk(tmp_path, "99999", "1", "sdk-key-v4", require_opengl=True)


def test_sdk_checkpoint_rejects_source_lock_and_manifest_tampering(tmp_path: Path) -> None:
    _sealed_fixture(tmp_path)
    metadata_path = tmp_path / METADATA_NAME
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["source_lock_sha256"] = "0" * 64
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
    with pytest.raises(ValueError, match="identity"):
        validate_sdk(tmp_path, "12345", "1", "sdk-key-v4", require_opengl=True)

    _sealed_fixture(tmp_path)
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["files"][0]["sha256"] = "0" * 64
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
    with pytest.raises(ValueError, match="hash/size"):
        validate_sdk(tmp_path, "12345", "1", "sdk-key-v4", require_opengl=True)


def test_sdk_checkpoint_rejects_a_partial_opengl_sdk(tmp_path: Path) -> None:
    _sealed_fixture(tmp_path)
    (tmp_path / "win64/vc14/bin/TKOpenGl.dll").unlink()
    with pytest.raises(ValueError, match="canonical Windows OpenGL paths"):
        validate_sdk(tmp_path, "12345", "1", "sdk-key-v4", require_opengl=True)


def test_legacy_sdk_cannot_satisfy_opengl_consumer_contract(tmp_path: Path) -> None:
    _sealed_fixture(tmp_path)
    metadata_path = tmp_path / METADATA_NAME
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["schema_version"] = 1
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
    with pytest.raises(ValueError, match="USE_OPENGL=ON"):
        validate_sdk(tmp_path, "12345", "1", "sdk-key-v4", require_opengl=True)


def test_real_nested_windows_layout_passes_producer_consumer_and_scanner(tmp_path: Path) -> None:
    result = run_smoke()
    assert result["status"] == "PASS"
    assert result["producer_post_install"] == "PASS"
    assert result["consumer_validator"] == "PASS"
    assert result["downstream_dependency_scanner"] == "PASS"
    _sealed_fixture(tmp_path)
    validate_sdk(tmp_path, "12345", "1", "sdk-key-v4", require_opengl=True)


@pytest.mark.parametrize("relative", CANONICAL_OPENGL_FILES)
def test_producer_rejects_each_missing_canonical_file(tmp_path: Path, relative: str) -> None:
    _sealed_fixture(tmp_path)
    (tmp_path / Path(relative)).unlink()
    with pytest.raises(ValueError, match="lacks canonical Windows OpenGL paths"):
        validate_installed_sdk(tmp_path)


def test_producer_rejects_flattened_only_layout(tmp_path: Path) -> None:
    _sealed_fixture(tmp_path)
    for relative in CANONICAL_OPENGL_FILES[1:]:
        original = tmp_path / Path(relative)
        flat = tmp_path / Path(relative).name
        flat.parent.mkdir(parents=True, exist_ok=True)
        original.replace(flat)
    with pytest.raises(ValueError, match="lacks canonical Windows OpenGL paths"):
        validate_installed_sdk(tmp_path)


def test_producer_rejects_wrong_cmake_export_and_case_collision(tmp_path: Path) -> None:
    _sealed_fixture(tmp_path)
    config = tmp_path / "cmake/OpenCASCADEConfig.cmake"
    config.write_text(config.read_text().replace("win64/vc14/lib", "lib"), encoding="utf-8")
    with pytest.raises(ValueError, match="incorrect opencascade_library_dir"):
        validate_installed_sdk(tmp_path)


def test_producer_rejects_sdk_symlink(tmp_path: Path) -> None:
    _sealed_fixture(tmp_path)
    link = tmp_path / "inc/header-link.hxx"
    try:
        os.symlink(tmp_path / "inc/OpenGl_Context.hxx", link)
    except (OSError, NotImplementedError):
        pytest.skip("symbolic links are unavailable in this environment")
    with pytest.raises(ValueError, match="symbolic link"):
        validate_installed_sdk(tmp_path)


def test_consumer_rejects_wrong_flags_and_unsafe_manifest_paths(tmp_path: Path) -> None:
    _sealed_fixture(tmp_path)
    metadata_path = tmp_path / METADATA_NAME
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["cmake_options"]["USE_OPENGL"] = False
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
    with pytest.raises(ValueError, match="CMake option contract"):
        validate_sdk(tmp_path, "12345", "1", "sdk-key-v4", require_opengl=True)

    _sealed_fixture(tmp_path)
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["files"][0]["relative_path"] = "../escape"
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
    with pytest.raises(ValueError, match="unsafe or duplicate"):
        validate_sdk(tmp_path, "12345", "1", "sdk-key-v4", require_opengl=True)


def test_consumer_rejects_casefold_duplicate_manifest_records(tmp_path: Path) -> None:
    _sealed_fixture(tmp_path)
    metadata_path = tmp_path / METADATA_NAME
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    duplicate = dict(metadata["files"][0])
    duplicate["relative_path"] = duplicate["relative_path"].swapcase()
    metadata["files"].append(duplicate)
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
    with pytest.raises(ValueError, match="unsafe or duplicate"):
        validate_sdk(tmp_path, "12345", "1", "sdk-key-v4", require_opengl=True)
