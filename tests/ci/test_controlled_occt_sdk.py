from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from tools.packaging.validate_controlled_occt_sdk import METADATA_NAME, validate_sdk


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sealed_fixture(root: Path) -> None:
    payloads = {
        "bin/TKernel.dll": b"runtime",
        "lib/TKernel.lib": b"import library",
        "cmake/OpenCASCADEConfig.cmake": b"set(OpenCASCADE_VERSION 7.9.3)",
    }
    entries = []
    for relative, payload in payloads.items():
        target = root / Path(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
        entries.append(
            {"relative_path": relative, "byte_length": len(payload), "sha256": _digest(payload)}
        )
    from tools.packaging.build_controlled_occt_sdk import LOCK, OCCT_ID
    from tools.packaging.validate_windows_native_source_lock import load_source_lock

    record = next(row for row in load_source_lock(LOCK)["records"] if row["id"] == OCCT_ID)
    payload = json.dumps(entries, sort_keys=True, separators=(",", ":")).encode("utf-8")
    (root / METADATA_NAME).write_text(
        json.dumps(
            {
                "schema_version": 1,
                "status": "SEALED",
                "stage": "occt-sdk",
                "producer_job_id": "occt-sdk",
                "producer_run_id": "12345",
                "producer_run_attempt": "1",
                "cache_key": "sdk-key-v1",
                "payload_sha256": _digest(payload),
                "source_lock_sha256": _digest(LOCK.read_bytes()),
                "occt_source_id": OCCT_ID,
                "occt_source_revision": record["revision"],
                "occt_source_sha256": record["sha256"],
                "windows_sdk": "10.0.26100.0",
                "python": "3.12.15",
                "cmake": "cmake version 3.31.8",
                "compiler": "MSVC 19.44.35229.0",
                "parallelism": 4,
                "file_count": len(entries),
                "byte_count": sum(entry["byte_length"] for entry in entries),
                "files": entries,
            }
        ),
        encoding="utf-8",
    )


def test_sdk_checkpoint_validates_run_identity_and_every_file(tmp_path: Path) -> None:
    _sealed_fixture(tmp_path)
    result = validate_sdk(tmp_path, "12345", "1", "sdk-key-v1")
    assert result["file_count"] == 3


def test_sdk_checkpoint_rejects_tampered_or_extra_files(tmp_path: Path) -> None:
    _sealed_fixture(tmp_path)
    (tmp_path / "bin/TKernel.dll").write_bytes(b"tampered")
    with pytest.raises(ValueError, match="hash/size"):
        validate_sdk(tmp_path, "12345", "1", "sdk-key-v1")
    (tmp_path / "bin/TKernel.dll").write_bytes(b"runtime")
    (tmp_path / "extra.dll").write_bytes(b"unlisted")
    with pytest.raises(ValueError, match="file set"):
        validate_sdk(tmp_path, "12345", "1", "sdk-key-v1")


def test_sdk_checkpoint_rejects_another_producer_run(tmp_path: Path) -> None:
    _sealed_fixture(tmp_path)
    with pytest.raises(ValueError, match="identity"):
        validate_sdk(tmp_path, "99999", "1", "sdk-key-v1")
