"""PL-0418 synthetic dry-run: off-machine scan copies are verified byte-for-byte."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from tools.dev.scan_copy_manifest import create_manifest, main, verify_copy


def _scan_folder(root: Path) -> Path:
    source = root / "SYNTHETIC-TEST-PKG-0001"
    (source / "captures").mkdir(parents=True)
    (source / "captures" / "SYNTHETIC-TEST-CAP-0001.packscan").write_bytes(b"\x00synthetic" * 50)
    (source / "project.json").write_text('{"synthetic": true}', encoding="utf-8")
    return source


def test_identical_copy_passes_and_cli_reports_it(tmp_path: Path, capsys) -> None:
    source = _scan_folder(tmp_path)
    copy = tmp_path / "offsite" / source.name
    shutil.copytree(source, copy)
    manifest = tmp_path / "manifest.json"
    assert main(["create", str(source), str(manifest)]) == 0
    assert json.loads(manifest.read_text(encoding="utf-8"))["file_count"] == 2
    assert main(["verify", str(manifest), str(copy)]) == 0
    assert "SCAN_COPY_VERIFY_PASS" in capsys.readouterr().out
    assert main(["create", str(source), str(manifest)]) == 2  # never overwrites


def test_missing_extra_and_bit_flipped_files_fail(tmp_path: Path) -> None:
    source = _scan_folder(tmp_path)
    manifest = create_manifest(source)
    copy = tmp_path / "copy"
    shutil.copytree(source, copy)
    capture = copy / "captures" / "SYNTHETIC-TEST-CAP-0001.packscan"
    data = bytearray(capture.read_bytes())
    data[3] ^= 0x01  # same size, one bit altered
    capture.write_bytes(bytes(data))
    (copy / "project.json").unlink()
    (copy / "stray.tmp").write_bytes(b"x")
    assert verify_copy(manifest, copy) == [
        "missing: project.json",
        "unexpected: stray.tmp",
        "altered: captures/SYNTHETIC-TEST-CAP-0001.packscan",
    ]
    assert verify_copy({"contract": "other"}, copy) == ["manifest_invalid"]
    assert verify_copy(manifest, tmp_path / "absent")[0].startswith("copy_unreadable")
