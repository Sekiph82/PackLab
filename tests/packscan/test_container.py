"""Focused PackScan container integrity and ZIP-boundary tests."""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import pytest

from packlab_core.packscan import PackScanError, read_packscan, write_packscan

CANONICALIZATION = "sha256_32_bytes_lowercase_hex_64_chars_v1"


def _manifest(
    repo_root: Path, *, image_size: int = 3, image_sha: str | None = None
) -> dict[str, object]:
    source = repo_root / "tests" / "fixtures" / "packscan" / "manifest-valid.json"
    value = json.loads(source.read_text(encoding="utf-8"))
    payloads = value["payloads"]
    assert isinstance(payloads, list)
    image = payloads[0]
    metadata = payloads[1]
    assert isinstance(image, dict) and isinstance(metadata, dict)
    image["size_bytes"] = image_size
    image["sha256"] = image_sha or hashlib.sha256(b"IMG").hexdigest()
    metadata["size_bytes"] = 2
    metadata["sha256"] = hashlib.sha256(b"{}").hexdigest()
    return value


def _write_raw(path: Path, files: dict[str, bytes]) -> None:
    checksums = {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}
    files = dict(files)
    files["checksums.json"] = (
        json.dumps(
            {
                "schema_version": "1.0.0",
                "algorithm": "sha256",
                "canonicalization": CANONICALIZATION,
                "entries": checksums,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        order = [
            name
            for name in ["manifest.json", "metadata/photos.json", "checksums.json"]
            if name in files
        ]
        order += sorted(name for name in files if name not in order)
        for name in order:
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, files[name], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def _valid_files(manifest: dict[str, object]) -> dict[str, bytes]:
    return {
        "manifest.json": (
            json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n"
        ).encode("utf-8"),
        "images/0001.jpg": b"IMG",
        "metadata/photos.json": b"{}",
    }


def test_writer_is_deterministic_and_reader_returns_validated_payloads(
    tmp_path: Path, repo_root: Path
) -> None:
    manifest = _manifest(repo_root)
    payloads = {"images/0001.jpg": b"IMG", "metadata/photos.json": b"{}"}
    first = write_packscan(tmp_path / "first.packscan", manifest, payloads)
    second = write_packscan(tmp_path / "second.packscan", manifest, payloads)
    assert first.read_bytes() == second.read_bytes()
    report = read_packscan(first)
    assert report.payloads == payloads
    assert (
        report.checksums["manifest.json"]
        == hashlib.sha256(
            json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
                "utf-8"
            )
            + b"\n"
        ).hexdigest()
    )


def test_authoritative_checksum_mismatch_is_distinguished(tmp_path: Path, repo_root: Path) -> None:
    manifest = _manifest(repo_root, image_size=7, image_sha=hashlib.sha256(b"ORIGINAL").hexdigest())
    files = _valid_files(manifest)
    files["images/0001.jpg"] = b"ALTERED"
    _write_raw(tmp_path / "authoritative-mismatch.packscan", files)
    with pytest.raises(PackScanError, match="checksum_mismatch_authoritative"):
        read_packscan(tmp_path / "authoritative-mismatch.packscan")


def test_truncated_entry_is_distinguished(tmp_path: Path, repo_root: Path) -> None:
    manifest = _manifest(repo_root, image_size=5, image_sha=hashlib.sha256(b"12345").hexdigest())
    _write_raw(
        tmp_path / "truncated.packscan",
        {**_valid_files(manifest), "images/0001.jpg": b"12"},
    )
    with pytest.raises(PackScanError, match="truncated_entry"):
        read_packscan(tmp_path / "truncated.packscan")


def test_missing_extra_duplicate_and_traversal_entries_are_rejected(
    tmp_path: Path, repo_root: Path
) -> None:
    manifest = _manifest(repo_root)
    valid = _valid_files(manifest)
    missing = dict(valid)
    missing.pop("metadata/photos.json")
    _write_raw(tmp_path / "missing-control.packscan", missing)
    with pytest.raises(PackScanError, match="missing_entry"):
        read_packscan(tmp_path / "missing-control.packscan")

    extra = dict(valid)
    extra["diagnostics/undeclared.json"] = b"{}"
    _write_raw(tmp_path / "extra.packscan", extra)
    with pytest.raises(PackScanError, match="extra_entry"):
        read_packscan(tmp_path / "extra.packscan")

    duplicate_path = tmp_path / "duplicate.packscan"
    with zipfile.ZipFile(duplicate_path, "w") as archive:
        info = zipfile.ZipInfo("../escape.bin", date_time=(1980, 1, 1, 0, 0, 0))
        archive.writestr(info, b"bad")
        archive.writestr("images/0001.jpg", b"bad")
    with pytest.raises(PackScanError, match="unsafe_path"):
        read_packscan(duplicate_path)


def test_exact_and_casefold_duplicate_names_are_rejected(tmp_path: Path) -> None:
    path = tmp_path / "duplicates.packscan"
    with zipfile.ZipFile(path, "w") as archive:
        for name in ("images/0001.jpg", "images/0001.jpg"):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            archive.writestr(info, b"x")
    with pytest.raises(PackScanError, match="duplicate_entry"):
        read_packscan(path)


def test_optional_derived_payloads_are_safe_when_omitted(tmp_path: Path, repo_root: Path) -> None:
    manifest = _manifest(repo_root)
    report = read_packscan(
        write_packscan(
            tmp_path / "omitted-derived.packscan",
            manifest,
            {"images/0001.jpg": b"IMG", "metadata/photos.json": b"{}"},
        )
    )
    assert not any(path.startswith(("previews/", "diagnostics/")) for path in report.payloads)
