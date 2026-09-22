"""Windows-runnable compatibility checks for the committed Swift writer contract."""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import pytest

from packlab_core.packscan import PackScanError, read_packscan, write_packscan


def _swift_input(repo_root: Path) -> tuple[dict[str, object], dict[str, bytes], dict[str, object]]:
    fixture_dir = repo_root / "tests" / "fixtures" / "packscan"
    fixture = json.loads(
        (fixture_dir / "swift-writer-contract-fixture.json").read_text(encoding="utf-8")
    )
    manifest = json.loads((fixture_dir / "manifest-valid.json").read_text(encoding="utf-8"))
    payloads = {"images/0001.jpg": b"IMG", "metadata/photos.json": b"{}"}
    declared = manifest["payloads"]
    assert isinstance(declared, list)
    for item in declared:
        assert isinstance(item, dict)
        data = payloads[item["path"]]
        item["size_bytes"] = len(data)
        item["sha256"] = hashlib.sha256(data).hexdigest()
    return manifest, payloads, fixture


def test_swift_contract_fixture_validates_as_python_packscan(
    tmp_path: Path, repo_root: Path
) -> None:
    manifest, payloads, fixture = _swift_input(repo_root)
    package = write_packscan(tmp_path / "swift-contract.packscan", manifest, payloads)
    report = read_packscan(package)
    with zipfile.ZipFile(package) as archive:
        infos = archive.infolist()
        assert [info.filename for info in infos] == fixture["expected_entry_order"]
        assert all(info.compress_type == zipfile.ZIP_DEFLATED for info in infos)
        assert all(info.date_time == (1980, 1, 1, 0, 0, 0) for info in infos)
        assert all(info.extra == b"" for info in infos)
        assert json.loads(archive.read("metadata/photos.json")) == {}
        checksum_index = json.loads(archive.read("checksums.json"))
        assert set(checksum_index["entries"]) == {
            info.filename for info in infos if info.filename != "checksums.json"
        }
    assert report.manifest["schema_version"] == "1.0.0"
    assert report.payloads == payloads


def test_python_rejects_swift_contract_negative_manifest_hash_mutation(
    tmp_path: Path, repo_root: Path
) -> None:
    manifest, payloads, _ = _swift_input(repo_root)
    package = write_packscan(tmp_path / "swift-contract.packscan", manifest, payloads)
    with zipfile.ZipFile(package) as source:
        files = {name: source.read(name) for name in source.namelist()}
    mutated = json.loads(files["manifest.json"])
    mutated["payloads"][0]["sha256"] = hashlib.sha256(b"different-bytes").hexdigest()
    files["manifest.json"] = (
        json.dumps(mutated, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode()
    checksum_entries = {
        name: hashlib.sha256(data).hexdigest()
        for name, data in files.items()
        if name != "checksums.json"
    }
    files["checksums.json"] = (
        json.dumps(
            {
                "schema_version": "1.0.0",
                "algorithm": "sha256",
                "canonicalization": "sha256_32_bytes_lowercase_hex_64_chars_v1",
                "entries": checksum_entries,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode()
    mutated_package = tmp_path / "swift-contract-mutated.packscan"
    with zipfile.ZipFile(
        mutated_package, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archive:
        for name in ["manifest.json", "metadata/photos.json", "checksums.json", "images/0001.jpg"]:
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, files[name], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    with pytest.raises(PackScanError, match="checksum_mismatch_authoritative"):
        read_packscan(mutated_package)
