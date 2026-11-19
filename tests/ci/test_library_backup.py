"""PL-0412 synthetic dry-run: library backup sets restore byte-exact and re-open semantically.

SIMULATION ONLY: every library here is generated under tmp_path with SYNTHETIC ids. Nothing
below is a real Kenya library, a real storage medium or a clean-machine restore.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pytest
from tests.core.test_packaging_asset import _asset
from tools.dev import library_backup
from tools.dev.library_backup import (
    LibraryBackupError,
    create_backup,
    main,
    restore_backup,
    verify_restored,
)

from packlab_core.packaging_sku_library import PackagingSkuRevision, PackagingSkuStatus
from packlab_studio.packaging_library_audit import PackagingLibraryAuditStore
from packlab_studio.packaging_library_store import AttachmentRole, PackagingLibraryStore

_NOW = datetime(2026, 11, 19, 12, 0, tzinfo=UTC)


def _library(root: Path, scratch: Path) -> Path:
    audit = PackagingLibraryAuditStore(root, clock=lambda: _NOW)
    asset = _asset(asset_id="SYNTHETIC-asset-0001", display_name="Synthetic 500 mL bottle")
    created = audit.create_asset(
        asset,
        expected_state_revision=audit.snapshot().state_revision,
        actor_id="synthetic-operator",
        reason="Synthetic PL-0412 fixture",
    )
    sku = PackagingSkuRevision.create(
        asset,
        sku_id="SYNTHETIC-sku-0001",
        display_name="Synthetic SKU",
        status=PackagingSkuStatus.ACTIVE,
    )
    audit.create_sku(
        sku,
        expected_state_revision=created.state_revision,
        expected_asset_revision_id=created.assets[0].revision_id,
        actor_id="synthetic-operator",
        reason="Synthetic PL-0412 SKU binding",
    )
    drawing = scratch / "synthetic-drawing.pdf"
    drawing.write_bytes(b"%PDF synthetic drawing " * 40)
    PackagingLibraryStore(root).add_attachment(
        drawing,
        display_name="synthetic drawing.pdf",
        media_type="application/pdf",
        role=AttachmentRole.DRAWING,
        related_asset_id=asset.asset_id,
        assets=(asset,),
    )
    (root / "captures").mkdir()
    (root / "captures" / "SYNTHETIC-CAP-0001.packscan").write_bytes(bytes(range(256)) * 8)
    return root


@pytest.fixture
def backup(tmp_path: Path) -> tuple[Path, dict]:
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    library = _library(tmp_path / "library", scratch)
    backup_set = tmp_path / "backups" / "set-1"
    return backup_set, create_backup(library, backup_set)


def _writable(path: Path) -> Path:
    for directory, _, names in os.walk(path):
        for name in names:
            os.chmod(os.path.join(directory, name), 0o644)
    return path


def test_round_trip_restores_and_reopens_the_library(tmp_path: Path, backup) -> None:
    backup_set, manifest = backup
    library = manifest["library"]
    assert set(library["sku_bindings"]) == {"SYNTHETIC-sku-0001"}
    assert (
        library["sku_bindings"]["SYNTHETIC-sku-0001"]["packaging_asset_id"]
        in (library["asset_revisions"])
    )
    assert len(library["attachment_ids"]) == 1
    assert manifest["files"]["file_count"] == 5  # state, record, blob, capture + lock file
    with pytest.raises(LibraryBackupError, match="immutable"):
        create_backup(tmp_path / "library", backup_set)

    target = tmp_path / "restored"
    report = restore_backup(
        backup_set, target, expected_manifest_sha256=manifest["manifest_sha256"]
    )
    assert report["verdict"] == "PASS", report
    assert report["semantic_check"] == "library_reopened"
    assert report["library_state_revision"] == library["state_revision"]
    snapshot = PackagingLibraryAuditStore(target).validate()
    assert snapshot.skus[0].packaging_asset_revision_id == snapshot.assets[0].revision_id
    capture = target / "captures" / "SYNTHETIC-CAP-0001.packscan"
    assert not os.access(capture, os.W_OK)  # restored read-only
    assert main(["verify", str(backup_set), str(target)]) == 0


def test_backup_and_report_are_deterministic(tmp_path: Path, backup) -> None:
    backup_set, manifest = backup
    again = create_backup(tmp_path / "library", tmp_path / "backups" / "set-2")
    assert again == manifest
    assert (backup_set / "manifest.json").read_bytes() == (
        tmp_path / "backups" / "set-2" / "manifest.json"
    ).read_bytes()
    assert str(tmp_path) not in (backup_set / "manifest.json").read_text(encoding="utf-8")
    first = restore_backup(backup_set, tmp_path / "r1")
    second = restore_backup(tmp_path / "backups" / "set-2", tmp_path / "r2")
    assert first == second and first["verdict"] == "PASS"


CAPTURE = "data/captures/SYNTHETIC-CAP-0001.packscan"


def _flip(path: Path) -> None:
    data = bytearray(path.read_bytes())
    data[10] ^= 0x01
    path.write_bytes(bytes(data))


@pytest.mark.parametrize(
    ("corrupt", "reason"),
    [
        (lambda s: (s / CAPTURE).unlink(), "missing: captures/SYNTHETIC-CAP-0001.packscan"),
        (lambda s: (s / "data/stray.bin").write_bytes(b"x"), "unexpected: stray.bin"),
        (
            lambda s: (s / CAPTURE).write_bytes((s / CAPTURE).read_bytes()[:-1]),
            "truncated: captures/SYNTHETIC-CAP-0001.packscan",
        ),
        (lambda s: _flip(s / CAPTURE), "altered: captures/SYNTHETIC-CAP-0001.packscan"),
        (
            lambda s: (s / CAPTURE).rename(s / "data/captures/renamed.packscan"),
            "renamed: captures/SYNTHETIC-CAP-0001.packscan -> captures/renamed.packscan",
        ),
    ],
)
def test_each_corruption_class_fails_and_publishes_nothing(
    tmp_path: Path, backup, corrupt, reason
) -> None:
    backup_set, _ = backup
    corrupt(_writable(backup_set))
    target = tmp_path / "restored"
    report = restore_backup(backup_set, target)
    assert report["verdict"] == "FAIL"
    assert report["reasons"] == [reason]
    assert not target.exists()
    assert not [p for p in tmp_path.iterdir() if p.name.startswith(".restored.restore-")]


def test_corruption_after_restore_is_detected(tmp_path: Path, backup) -> None:
    backup_set, _ = backup
    target = tmp_path / "restored"
    assert restore_backup(backup_set, target, read_only=False)["verdict"] == "PASS"
    _flip(target / "captures" / "SYNTHETIC-CAP-0001.packscan")
    assert verify_restored(backup_set, target)["reasons"] == [
        "altered: captures/SYNTHETIC-CAP-0001.packscan"
    ]


def _rewrite_manifest(backup_set: Path, edit) -> dict:
    path = _writable(backup_set) / "manifest.json"
    manifest = json.loads(path.read_bytes())
    edit(manifest)
    body = {k: v for k, v in manifest.items() if k != "manifest_sha256"}
    manifest["manifest_sha256"] = library_backup._sha256(body)  # attacker re-signs
    path.write_bytes(library_backup._canonical(manifest))
    return manifest


@pytest.mark.parametrize("bad", ["../escape.bin", "/abs.bin", "C:/abs.bin", "a\\..\\b", "a//b"])
def test_tampered_manifest_paths_are_rejected(tmp_path: Path, backup, bad: str) -> None:
    backup_set, _ = backup
    _rewrite_manifest(backup_set, lambda m: m["files"]["files"][0].update(path=bad))
    report = restore_backup(backup_set, tmp_path / "restored")
    assert report["verdict"] == "FAIL"
    assert f"manifest_path_unsafe: {bad!r}" in report["reasons"]
    assert not (tmp_path / "escape.bin").exists() and not (tmp_path / "restored").exists()


def test_manifest_digest_binds_semantics_and_offband_digest(tmp_path: Path, backup) -> None:
    backup_set, original = backup
    path = _writable(backup_set) / "manifest.json"
    raw = path.read_bytes()
    path.write_bytes(raw.replace(b'"tool_version"', b'"tool_versiom"'))
    assert "manifest_digest_mismatch" in restore_backup(backup_set, tmp_path / "a")["reasons"]
    path.write_bytes(raw)
    # A re-signed manifest with altered revisions passes bytes but fails semantically ...
    forged = _rewrite_manifest(
        backup_set, lambda m: m["library"].update(state_revision="forged-revision")
    )
    report = restore_backup(backup_set, tmp_path / "b")
    assert report["reasons"] == ["semantic_mismatch: state_revision"]
    assert not (tmp_path / "b").exists()
    # ... and is rejected outright when the work-record digest is supplied.
    report = restore_backup(
        backup_set, tmp_path / "c", expected_manifest_sha256=original["manifest_sha256"]
    )
    assert report["reasons"] == ["manifest_digest_not_expected"]
    assert forged["manifest_sha256"] != original["manifest_sha256"]


def test_half_written_backup_without_manifest_never_verifies(tmp_path: Path, backup) -> None:
    backup_set, _ = backup
    (_writable(backup_set) / "manifest.json").unlink()
    assert restore_backup(backup_set, tmp_path / "r")["reasons"] == ["manifest_unreadable"]


def test_crash_during_backup_leaves_no_backup_set(tmp_path: Path, monkeypatch) -> None:
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    library = _library(tmp_path / "library", scratch)
    real_copy = library_backup._copy_verified
    calls = []

    def crash_on_third(*args):
        calls.append(args)
        if len(calls) == 3:
            raise KeyboardInterrupt("simulated crash")
        real_copy(*args)

    monkeypatch.setattr(library_backup, "_copy_verified", crash_on_third)
    with pytest.raises(KeyboardInterrupt):
        create_backup(library, tmp_path / "backups" / "set-1")
    assert list((tmp_path / "backups").iterdir()) == []
    monkeypatch.undo()
    assert create_backup(library, tmp_path / "backups" / "set-1")["manifest_sha256"]


def test_crash_during_restore_leaves_target_absent(tmp_path: Path, backup, monkeypatch) -> None:
    backup_set, _ = backup

    def crash(*args):
        raise KeyboardInterrupt("simulated crash")

    monkeypatch.setattr(library_backup, "_copy_verified", crash)
    with pytest.raises(KeyboardInterrupt):
        restore_backup(backup_set, tmp_path / "restored")
    assert not (tmp_path / "restored").exists()
    assert not [p for p in tmp_path.iterdir() if p.name.startswith(".restored")]


def test_non_empty_target_and_bounds_are_refused(tmp_path: Path, backup) -> None:
    backup_set, _ = backup
    target = tmp_path / "occupied"
    target.mkdir()
    (target / "keep.txt").write_text("owner data", encoding="utf-8")
    with pytest.raises(LibraryBackupError, match="empty"):
        restore_backup(backup_set, target)
    assert (target / "keep.txt").read_text(encoding="utf-8") == "owner data"
    (tmp_path / "empty").mkdir()
    assert restore_backup(backup_set, tmp_path / "empty")["verdict"] == "PASS"
    with pytest.raises(LibraryBackupError, match="file count"):
        create_backup(tmp_path / "library", tmp_path / "small", max_files=2)
    with pytest.raises(LibraryBackupError, match="total bytes"):
        create_backup(tmp_path / "library", tmp_path / "small", max_bytes=100)
    with pytest.raises(LibraryBackupError, match="overlap"):
        create_backup(tmp_path / "library", tmp_path / "library" / "inside")
    assert not (tmp_path / "small").exists()


def _junction(link: Path, target: Path) -> bool:
    if os.name != "nt":
        return False
    result = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(link), str(target)], capture_output=True, check=False
    )
    return result.returncode == 0 and os.path.isjunction(link)


def _link(link: Path, target: Path) -> str:
    if _junction(link, target):
        return "junction"
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip("neither junctions nor symlinks can be created here")
    return "symlink"


def test_links_inside_root_and_in_ancestors_are_refused(tmp_path: Path) -> None:
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    library = _library(tmp_path / "library", scratch)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.bin").write_bytes(b"not part of the library")
    _link(library / "linked", outside)
    with pytest.raises(LibraryBackupError, match="link refused"):
        create_backup(library, tmp_path / "set-a")
    os.unlink(library / "linked") if os.name != "nt" else (library / "linked").rmdir()
    _link(tmp_path / "parent-link", tmp_path)
    with pytest.raises(LibraryBackupError, match="symlink or junction"):
        create_backup(tmp_path / "parent-link" / "library", tmp_path / "set-b")
    assert not (tmp_path / "set-a").exists() and not (tmp_path / "set-b").exists()


def test_unreadable_entry_is_refused(tmp_path: Path, monkeypatch) -> None:
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    library = _library(tmp_path / "library", scratch)
    real_scandir = os.scandir

    def failing_scandir(path):
        if str(path).endswith("captures"):
            raise PermissionError(13, "synthetic access denied", str(path))
        return real_scandir(path)

    monkeypatch.setattr(os, "scandir", failing_scandir)
    with pytest.raises(LibraryBackupError, match="unreadable"):
        create_backup(library, tmp_path / "set")
    assert not (tmp_path / "set").exists()


def test_plain_folder_without_library_state_is_bytes_only(tmp_path: Path) -> None:
    source = tmp_path / "scan"
    source.mkdir()
    (source / "SYNTHETIC-raw.bin").write_bytes(b"synthetic")
    manifest = create_backup(source, tmp_path / "set")
    assert manifest["library"] is None
    report = restore_backup(tmp_path / "set", tmp_path / "restored")
    assert (report["verdict"], report["semantic_check"]) == ("PASS", "no_library_state")


def test_resigned_state_tampering_fails_the_real_library_loader(tmp_path: Path, backup) -> None:
    # Bytes and manifest are made consistent; only the semantic re-open can catch this.
    backup_set, _ = backup
    state = _writable(backup_set) / "data" / "packaging-library-state.json"
    value = json.loads(state.read_bytes())
    value["skus"][0]["document"]["display_name"] = "Tampered SKU"
    state.write_bytes(json.dumps(value).encode())
    data = state.read_bytes()

    def resign(manifest: dict) -> None:
        files = manifest["files"]
        entry = next(f for f in files["files"] if f["path"] == "packaging-library-state.json")
        entry.update(size=len(data), sha256=hashlib.sha256(data).hexdigest())
        files["total_bytes"] = sum(f["size"] for f in files["files"])

    _rewrite_manifest(backup_set, resign)
    report = restore_backup(backup_set, tmp_path / "restored")
    assert report["verdict"] == "FAIL"
    assert report["reasons"][0].startswith("semantic_load_failed: packaging_library_sku")
    assert not (tmp_path / "restored").exists()


# --- PL-0412 security review V01 fixes -------------------------------------------------------


@pytest.mark.parametrize("inside", ["data/inside", "x", "."])
def test_restore_target_overlapping_the_backup_set_is_refused(
    tmp_path: Path, backup, inside: str
) -> None:
    backup_set, _ = backup
    before = sorted(p.relative_to(backup_set) for p in backup_set.rglob("*"))
    expected = "missing or empty" if inside == "." else "overlap"
    with pytest.raises(LibraryBackupError, match=expected):
        restore_backup(backup_set, backup_set / inside)
    assert sorted(p.relative_to(backup_set) for p in backup_set.rglob("*")) == before
    assert restore_backup(backup_set, tmp_path / "clean")["verdict"] == "PASS"


def test_source_changing_between_manifest_and_copy_publishes_nothing(
    tmp_path: Path, monkeypatch
) -> None:
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    library = _library(tmp_path / "library", scratch)
    real_create = library_backup.create_manifest

    def create_then_change(root: Path) -> dict:
        manifest = real_create(root)
        _flip(root / "captures" / "SYNTHETIC-CAP-0001.packscan")
        return manifest

    monkeypatch.setattr(library_backup, "create_manifest", create_then_change)
    with pytest.raises(LibraryBackupError, match="file changed during copy"):
        create_backup(library, tmp_path / "backups" / "set-1")
    assert list((tmp_path / "backups").iterdir()) == []


def _resign_file(backup_set: Path, relative: str, data: bytes) -> None:
    path = _writable(backup_set) / "data" / relative
    path.write_bytes(data)

    def resign(manifest: dict) -> None:
        files = manifest["files"]
        entry = next(f for f in files["files"] if f["path"] == relative)
        entry.update(size=len(data), sha256=hashlib.sha256(data).hexdigest())
        files["total_bytes"] = sum(f["size"] for f in files["files"])

    _rewrite_manifest(backup_set, resign)


def test_resigned_attachment_blob_flip_fails_attachment_verification(
    tmp_path: Path, backup
) -> None:
    backup_set, manifest = backup
    blob = next(f["path"] for f in manifest["files"]["files"] if f["path"].startswith("attach"))
    data = bytearray((backup_set / "data" / blob).read_bytes())
    data[0] ^= 0x01
    _resign_file(backup_set, blob, bytes(data))
    report = restore_backup(backup_set, tmp_path / "restored")
    assert report["verdict"] == "FAIL"
    assert report["reasons"][0].startswith("semantic_load_failed: attachment does not verify")
    assert not (tmp_path / "restored").exists()


def test_resigned_deeply_nested_state_file_fails_instead_of_crashing(
    tmp_path: Path, backup
) -> None:
    backup_set, _ = backup
    _resign_file(backup_set, "packaging-library-state.json", b"[" * 200_000 + b"]" * 200_000)
    report = restore_backup(backup_set, tmp_path / "restored")
    assert report["verdict"] == "FAIL"
    assert report["reasons"][0].startswith("semantic_load_failed")


def _set_first_path(value: str):
    return lambda m: m["files"]["files"][0].update(path=value)


@pytest.mark.parametrize(
    ("edit", "reason"),
    [
        *[
            (_set_first_path(bad), f"manifest_path_unsafe: {bad!r}")
            for bad in ("a:b", "a\x07b", "CON", "d/aux.txt", "d/Com1.x", "trail.", "trail ")
        ],
        (
            lambda m: m["files"]["files"][0].update(path=m["files"]["files"][1]["path"].upper()),
            "manifest_path_case_collision",
        ),
        (lambda m: m.update(tool_version="9.9.9"), "manifest_tool_version_unsupported"),
        (lambda m: m.update(library="not-a-dict"), "manifest_library_invalid"),
    ],
)
def test_resigned_manifest_guards(tmp_path: Path, backup, edit, reason: str) -> None:
    backup_set, _ = backup
    _rewrite_manifest(backup_set, edit)
    report = restore_backup(backup_set, tmp_path / "restored")
    assert report["verdict"] == "FAIL" and reason in report["reasons"]
    assert verify_restored(backup_set, tmp_path / "restored")["verdict"] == "FAIL"
    assert not (tmp_path / "restored").exists()


@pytest.mark.parametrize(
    "raw",
    [b"[" * 200_000 + b"]" * 200_000, b'{"contract": NaN}', b'{"x": Infinity}'],
    ids=["deep-nesting", "nan", "infinity"],
)
def test_hostile_manifest_json_fails_instead_of_crashing(tmp_path: Path, backup, raw) -> None:
    backup_set, _ = backup
    (_writable(backup_set) / "manifest.json").write_bytes(raw)
    assert restore_backup(backup_set, tmp_path / "r")["reasons"] == ["manifest_unreadable"]
    assert main(["verify", str(backup_set), str(tmp_path / "r")]) == 1


def test_bounds_are_consistent_between_backup_and_restore(
    tmp_path: Path, backup, monkeypatch
) -> None:
    backup_set, _ = backup
    with pytest.raises(LibraryBackupError, match="unrestorable"):
        create_backup(tmp_path / "library", tmp_path / "big", max_files=10**9)
    (_writable(backup_set) / "data" / "stray.bin").write_bytes(b"x")
    monkeypatch.setattr(library_backup, "DEFAULT_MAX_FILES", 5)
    with pytest.raises(LibraryBackupError, match="file count"):
        restore_backup(backup_set, tmp_path / "r1")  # restore pre-walk of data/
    monkeypatch.setattr(library_backup, "DEFAULT_MAX_FILES", 4)
    assert "manifest_exceeds_bounds" in restore_backup(backup_set, tmp_path / "r2")["reasons"]


def test_backup_refuses_names_that_restore_would_reject(tmp_path: Path) -> None:
    source = tmp_path / "scan"
    source.mkdir()
    (source / "ok.bin").write_bytes(b"ok")
    try:
        (source / "aux.txt").write_bytes(b"device name on older Windows")
    except OSError:
        pytest.skip("platform maps aux.txt to a device")
    if not (source / "aux.txt").is_file():
        pytest.skip("platform maps aux.txt to a device")
    with pytest.raises(LibraryBackupError, match="restore would refuse"):
        create_backup(source, tmp_path / "set")
    assert not (tmp_path / "set").exists()


def test_backup_set_is_read_only_and_restore_writable_opt_out(tmp_path: Path, backup) -> None:
    backup_set, _ = backup
    assert not os.access(backup_set / "manifest.json", os.W_OK)
    assert not os.access(backup_set / CAPTURE, os.W_OK)
    assert main(["restore", str(backup_set), str(tmp_path / "rw"), "--writable"]) == 0
    assert os.access(tmp_path / "rw" / "captures" / "SYNTHETIC-CAP-0001.packscan", os.W_OK)


def test_final_reverify_catches_damage_after_publish(tmp_path: Path, backup, monkeypatch) -> None:
    backup_set, _ = backup
    real = library_backup._make_read_only

    def damage_then_lock(root: Path) -> None:
        _flip(root / "captures" / "SYNTHETIC-CAP-0001.packscan")
        real(root)

    monkeypatch.setattr(library_backup, "_make_read_only", damage_then_lock)
    report = restore_backup(backup_set, tmp_path / "restored")
    assert report["reasons"] == ["altered: captures/SYNTHETIC-CAP-0001.packscan"]


def test_restore_target_link_parent_file_and_linked_ancestor_are_refused(
    tmp_path: Path, backup
) -> None:
    backup_set, _ = backup
    (tmp_path / "empty").mkdir()
    _link(tmp_path / "target-link", tmp_path / "empty")
    with pytest.raises(LibraryBackupError, match="missing or empty"):
        restore_backup(backup_set, tmp_path / "target-link")
    (tmp_path / "a-file").write_bytes(b"x")
    with pytest.raises(LibraryBackupError, match="creatable"):
        restore_backup(backup_set, tmp_path / "a-file" / "restored")
    (tmp_path / "real-parent").mkdir()
    _link(tmp_path / "parent-link", tmp_path / "real-parent")
    with pytest.raises(LibraryBackupError, match="symlink or junction"):
        restore_backup(backup_set, tmp_path / "parent-link" / "restored")
    with pytest.raises(LibraryBackupError, match="symlink or junction"):
        create_backup(tmp_path / "library", tmp_path / "parent-link" / "set")
    assert list((tmp_path / "real-parent").iterdir()) == []
