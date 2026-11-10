"""PL-0418 synthetic dry-run: off-machine scan copies are verified byte-for-byte."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest
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


def _junction(link: Path, target: Path) -> bool:
    if os.name != "nt":
        return False
    result = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(link), str(target)], capture_output=True, check=False
    )
    return result.returncode == 0 and os.path.isjunction(link)


def test_copy_that_is_or_contains_a_link_back_to_the_source_fails(tmp_path: Path) -> None:
    source = _scan_folder(tmp_path)
    manifest = create_manifest(source)
    root_link = tmp_path / "root-link"
    if _junction(root_link, source):
        assert verify_copy(manifest, root_link)[0].startswith("copy_unreadable")
    else:
        root_link.symlink_to(source, target_is_directory=True)
        assert verify_copy(manifest, root_link)[0].startswith("copy_unreadable")
    nested = tmp_path / "nested"
    nested.mkdir()
    shutil.copy2(source / "project.json", nested / "project.json")
    if not _junction(nested / "captures", source / "captures"):
        (nested / "captures").symlink_to(source / "captures", target_is_directory=True)
    assert verify_copy(manifest, nested)[0].startswith("copy_unreadable: link refused")


@pytest.mark.parametrize(
    "broken",
    [
        lambda m: m.update(files=[]),
        lambda m: m.update(file_count=99),
        lambda m: m.update(total_bytes=1),
        lambda m: m["files"].append(m["files"][0]),
        lambda m: m["files"][0].pop("sha256"),
        lambda m: m["files"][0].update(size=True),
        lambda m: m["files"].__setitem__(0, "not-an-entry"),
    ],
)
def test_empty_inconsistent_or_malformed_manifests_are_invalid(tmp_path: Path, broken) -> None:
    source = _scan_folder(tmp_path)
    manifest = create_manifest(source)
    broken(manifest)
    assert verify_copy(manifest, source) == ["manifest_invalid"]


def test_empty_source_cannot_produce_a_manifest(tmp_path: Path) -> None:
    (tmp_path / "empty").mkdir()
    with pytest.raises(ValueError, match="no files"):
        create_manifest(tmp_path / "empty")


def test_copy_reached_through_a_linked_parent_folder_fails(tmp_path: Path) -> None:
    # Re-review P2-B: <junction-to-parent>/<source-name> resolves to the source itself.
    source = _scan_folder(tmp_path)
    manifest = create_manifest(source)
    parent_link = tmp_path / "parent-link"
    if not _junction(parent_link, source.parent):
        parent_link.symlink_to(source.parent, target_is_directory=True)
    result = verify_copy(manifest, parent_link / source.name)
    assert result[0].startswith("copy_unreadable: root path passes through")


def test_unreadable_subfolder_fails_instead_of_being_skipped(tmp_path: Path, monkeypatch) -> None:
    # Re-review P2-B: os.walk used to swallow errors, silently dropping files.
    source = _scan_folder(tmp_path)
    real_scandir = os.scandir

    def failing_scandir(path):
        if str(path).endswith("captures"):
            raise PermissionError(13, "synthetic access denied", str(path))
        return real_scandir(path)

    monkeypatch.setattr(os, "scandir", failing_scandir)
    with pytest.raises(ValueError, match="unreadable entry"):
        create_manifest(source)
