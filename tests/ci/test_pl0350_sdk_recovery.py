from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any

import pytest
from tools.packaging import recover_pl0350_sdk_artifacts as recovery


def _zip(path: Path, files: dict[str, bytes]) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content in files.items():
            archive.writestr(name, content)


def test_extract_zip_records_exact_bytes_and_hashes(tmp_path: Path) -> None:
    archive = tmp_path / "artifact.zip"
    _zip(archive, {"nested/payload.bin": b"verified-bytes"})

    records = recovery.extract_zip(archive, tmp_path / "out", 1024)

    assert records == [
        {
            "path": "nested/payload.bin",
            "byte_length": 14,
            "sha256": "35b1135247e25b36525c4f5bb88038cf310f05ab54aa450e406e9ef5c5fde911",
        }
    ]
    assert (tmp_path / "out/nested/payload.bin").read_bytes() == b"verified-bytes"


@pytest.mark.parametrize("member", ["../escape", "C:/escape"])
def test_extract_zip_rejects_unsafe_paths(tmp_path: Path, member: str) -> None:
    archive = tmp_path / "unsafe.zip"
    _zip(archive, {member: b"unsafe"})

    with pytest.raises(ValueError, match="Unsafe"):
        recovery.extract_zip(archive, tmp_path / "out", 1024)


def test_extract_zip_rejects_case_insensitive_duplicate(tmp_path: Path) -> None:
    archive = tmp_path / "duplicate.zip"
    _zip(archive, {"SDK/file.dll": b"one", "sdk/FILE.DLL": b"two"})

    with pytest.raises(ValueError, match="duplicate"):
        recovery.extract_zip(archive, tmp_path / "out", 1024)


def test_extract_zip_enforces_expanded_size_bound(tmp_path: Path) -> None:
    archive = tmp_path / "large.zip"
    _zip(archive, {"payload.bin": b"12345"})

    with pytest.raises(ValueError, match="expanded size"):
        recovery.extract_zip(archive, tmp_path / "out", 4)


def test_source_evidence_requires_exact_lock_and_record_bytes(tmp_path: Path) -> None:
    source_lock = recovery.Path("tools/packaging/windows_native_source_lock.json")
    lock = recovery.load_source_lock(source_lock)
    selected = [
        row
        for row in lock["records"]
        if row["source_availability_role"]
        in {
            "SOURCE_BUILD_INPUT",
            "CORRESPONDING_SOURCE_AND_NOTICES",
            "CORRESPONDING_SOURCE_AND_THIRD_PARTY_INVENTORY",
            "CORRESPONDING_SOURCE_AND_NOTICE",
        }
    ]
    records: list[dict[str, Any]] = [
        {
            "record_id": row["id"],
            "filename": row["url"].rsplit("/", 1)[-1],
            "expected_sha256": row["sha256"],
            "observed_sha256": row["sha256"],
            "byte_length": 1,
            "retained_runtime_surface": row["retained_runtime_surface"],
            "status": "PASS",
        }
        for row in selected
    ]
    evidence: dict[str, Any] = {
        "schema_version": 1,
        "source_lock_sha256": recovery.sha256(source_lock),
        "status": "PASS",
        "verified_source_count": len(records),
        "records": records,
    }
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps(evidence), encoding="utf-8")

    assert recovery.validate_source_evidence(path)["verified_source_count"] == len(records)
    evidence["records"][0]["observed_sha256"] = "0" * 64
    path.write_text(json.dumps(evidence), encoding="utf-8")
    with pytest.raises(ValueError, match="Source evidence differs"):
        recovery.validate_source_evidence(path)
