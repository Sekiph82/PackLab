"""PL-0482: scan part roles through import report, inbox, project and Studio pages."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from packlab_core.packscan import write_packscan
from packlab_studio import i18n
from packlab_studio.app import create_application
from packlab_studio.build_model import BuildModelView
from packlab_studio.capture_inbox import CaptureInboxView, parts_summary_text
from packlab_studio.navigation import Route
from packlab_studio.project import ProjectError, ProjectManager
from packlab_studio.receiver_session import InboxEntry, ReceiverSession
from packlab_studio.shell import StudioMainWindow

DIGEST = "a" * 64


def _package(path: Path, repo_root: Path, capture_id: str, role: str | None) -> Path:
    manifest = json.loads(
        (repo_root / "tests/fixtures/packscan/manifest-valid.json").read_text(encoding="utf-8")
    )
    manifest["capture_id"] = capture_id
    if role is not None:
        manifest["part_role"] = role
    image = capture_id.encode()
    manifest["payloads"][0]["size_bytes"] = len(image)
    manifest["payloads"][0]["sha256"] = hashlib.sha256(image).hexdigest()
    manifest["payloads"][1]["size_bytes"] = 2
    manifest["payloads"][1]["sha256"] = hashlib.sha256(b"{}").hexdigest()
    return write_packscan(path, manifest, {"images/0001.jpg": image, "metadata/photos.json": b"{}"})


def _session(root: Path) -> ReceiverSession:
    return ReceiverSession(
        root / "inbox",
        tls_root=root / "tls",
        port=0,
        bind_host="127.0.0.1",
        lan_host_provider=lambda: "127.0.0.1",
    )


def test_inbox_entry_carries_manifest_role_and_old_reports_are_assembled(
    tmp_path, repo_root
) -> None:
    session = _session(tmp_path)
    session.import_file(_package(tmp_path / "a.packscan", repo_root, "flip", "body_flipped"))
    session.import_file(_package(tmp_path / "b.packscan", repo_root, "legacy", None))
    roles = {entry.capture_id: entry.part_role for entry in session.entries()}
    assert roles == {"flip": "body_flipped", "legacy": "assembled"}
    record = next(r for r in session.index_records() if r.capture_id == "flip")
    report_path = session.data_root / str(record.report_location)
    report = json.loads(report_path.read_text("utf-8"))
    assert report["part_role"] == "body_flipped"
    # A report written before PL-0482 has no part_role: it reads as assembled.
    del report["part_role"]
    report_path.write_text(json.dumps(report), encoding="utf-8")
    fresh = _session(tmp_path)
    assert {e.capture_id: e.part_role for e in fresh.entries()}["flip"] == "assembled"


def test_project_records_roles_persists_and_undoes(tmp_path) -> None:
    manager = ProjectManager()
    manager.new_project(tmp_path / "project", "Jar")
    assert manager.scan_part_roles() == {}
    manager.set_scan_part_role(DIGEST, "closure")
    manager.set_scan_part_role("b" * 64, "body_interior")
    assert manager.scan_part_roles() == {DIGEST: "closure", "b" * 64: "body_interior"}
    revision = manager.metadata.revision
    manager.set_scan_part_role(DIGEST, "closure")  # unchanged: no new revision
    assert manager.metadata.revision == revision
    with pytest.raises(ProjectError):
        manager.set_scan_part_role(DIGEST, "lid")
    with pytest.raises(ProjectError):
        manager.set_scan_part_role("../x", "body")
    assert manager.undo() is not None
    assert manager.scan_part_roles() == {DIGEST: "closure"}
    assert manager.redo() is not None
    reopened = ProjectManager()
    reopened.open_project(tmp_path / "project")
    assert reopened.scan_part_roles() == {DIGEST: "closure", "b" * 64: "body_interior"}
    state = json.loads((tmp_path / "project/working/state.json").read_text("utf-8"))
    assert [e["reason"] for e in state["scan_part_role_events"]] == [
        "role_changed",
        "role_changed",
        "undo",
        "redo",
    ]
    reopened.undo()
    reopened.undo()
    assert reopened.scan_part_roles() == {}


def test_parts_summary_text_uses_project_overrides_and_turkish() -> None:
    entries = [
        InboxEntry(DIGEST, DIGEST, "imported", part_role="body"),
        InboxEntry("b", "b" * 64, "imported"),  # legacy: assembled
        InboxEntry("c", "c" * 64, "report unreadable", part_role="closure"),
    ]
    text = parts_summary_text(entries, {DIGEST: "body_flipped"})
    assert "Body: upright missing, upside down present, interior missing" in text
    assert "Assembled: upright present, upside down missing" in text
    assert "Closure: upright missing, upside down missing" in text
    try:
        i18n.set_language("tr")
        assert "Gövde: düz var, ters eksik, iç eksik" in parts_summary_text(entries, {})
    finally:
        i18n.set_language("en")


def test_capture_inbox_role_combo_saves_to_project_and_build_page_shows_role(
    monkeypatch, tmp_path, repo_root
) -> None:
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app = create_application(["packlab-part-roles-test"])
    package = _package(tmp_path / "lid.packscan", repo_root, "lid-scan", "closure")
    window = StudioMainWindow(
        receiver_session_factory=lambda: _session(tmp_path),
        diagnostics_root=tmp_path / "diagnostics",
        packaging_library_root=tmp_path / "library",
    )
    try:
        view = window.route_stack.views[Route.CAPTURE_INBOX]
        assert isinstance(view, CaptureInboxView)
        view._choose_file = lambda _parent: str(package)
        view.import_button.click()
        view.inbox_list.setCurrentRow(0)
        assert not view.role_combo.isEnabled()  # no project open: nowhere to save
        assert "Closure" in view.inbox_list.item(0).text()
        assert "Closure: upright present" in view.parts_label.text()

        window.project_manager.new_project(tmp_path / "project", "Jar")
        view.inbox_list.setCurrentRow(0)
        assert view.role_combo.isEnabled()
        assert view.role_combo.currentData() == "closure"
        view.role_combo.setCurrentIndex(view.role_combo.findData("closure_flipped"))
        view.role_combo.activated.emit(view.role_combo.currentIndex())
        digest = view._shown_entries[0].package_sha256
        assert window.project_manager.scan_part_roles() == {digest: "closure_flipped"}
        assert "Closure (upside down)" in view.inbox_list.item(0).text()
        assert "part_role: closure_flipped (manifest: closure)" in view.inbox_list.item(0).toolTip()
        assert "Closure: upright missing, upside down present" in view.parts_label.text()
        assert view.role_combo.currentData() == "closure_flipped"

        window.refresh_builds()
        builds = window.route_stack.views[Route.RECONSTRUCTION]
        assert isinstance(builds, BuildModelView)
        assert "Closure (upside down)" in builds.history.item(0).text()
        assert "Closure: upright missing, upside down present" in builds.parts_label.text()

        window.project_manager.undo()
        assert view.role_combo.currentData() == "closure"
        assert "Closure: upright present" in view.parts_label.text()
    finally:
        window.close()
        app.processEvents()
