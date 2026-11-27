"""PL-0490: Build 3D Model page shows live build states, the running builds and the queue."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from packlab_studio import i18n
from packlab_studio.app import create_application
from packlab_studio.build_model import BuildModelView, BuildResult, plain_failure
from packlab_studio.capture_inbox import parts_summary_text
from packlab_studio.jobs import JobManager
from packlab_studio.receiver_session import InboxEntry

CRASH = "stage exited 3221225477"


@pytest.fixture
def view(monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    create_application(["packlab-build-page-clarity-test"])
    return BuildModelView(JobManager())


def _entry(capture: str, role: str | None = None) -> InboxEntry:
    digest = hashlib.sha256(capture.encode()).hexdigest()
    if role is None:  # manifest without part_role: assembled, not declared
        return InboxEntry(capture, digest, "imported")
    return InboxEntry(capture, digest, "imported", part_role=role, role_declared=True)


def _workspace(root: Path, name: str, digest: str, state: str, reason: str | None = None) -> None:
    workspace = root / "working" / "reconstruction" / name
    workspace.mkdir(parents=True)
    manifest = {"source_digest": digest, "state": state, "reason": reason}
    (workspace / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


def _rows(view: BuildModelView) -> list[str]:
    return [view.history.item(row).text() for row in range(view.history.count())]


def test_scan_list_uses_live_job_state(view, tmp_path) -> None:
    jobs = view.jobs
    assert jobs is not None
    entries = [_entry(name) for name in ("aaaa1111", "bbbb2222", "cccc3333")]
    ids = [jobs.create(f"Build model {e.capture_id}", "reconstruction").job_id for e in entries]
    for job_id, entry in zip(ids, entries, strict=True):
        view.track(job_id, entry.capture_id)
    # The running build already has an active workspace: it is building, not interrupted.
    _workspace(tmp_path, "r1", entries[0].package_sha256, "active")
    view.refresh_history(entries, tmp_path)
    jobs.start(ids[0])
    jobs.update_progress(ids[0], 0.5, "5/8 Building the dense point cloud")
    rows = _rows(view)
    assert rows[0].endswith("building 50% - step 5/8 Building the dense point cloud")
    assert rows[1].endswith("queued #1") and rows[2].endswith("queued #2")
    # Header: the running build and the queue, not the last queued scan.
    assert view.title.text() == "Building 3D model of aaaa1111"
    assert "aaaa1111: building 50%" in view.status.text()
    assert "Queued: #1 bbbb2222, #2 cccc3333" in view.status.text()
    assert view.job_id == ids[0] and view.progress.value() == 50

    # Two concurrent builds: both show; texture crash fails in plain words.
    jobs.start(ids[1])
    assert view.title.text() == "Building 3D model of aaaa1111, bbbb2222"
    assert "bbbb2222: building 0%" in view.status.text()
    assert _rows(view)[2].endswith("queued #1")
    jobs.update_progress(ids[0], 0.875, "8/8 Texturing the mesh")
    jobs.fail(ids[0], CRASH)
    view.show_result(BuildResult(ids[0], "aaaa1111", "failed", f"Build failed: {CRASH}"))
    assert _rows(view)[0].endswith("failed: texture step (OpenMVS) crashed")
    assert view.title.text() == "Building 3D model of bbbb2222"
    assert "Last finished: Build failed: texture step (OpenMVS) crashed" in view.status.text()

    jobs.request_cancel(ids[2])  # cancelled while queued
    jobs.succeed(ids[1])
    view.show_result(BuildResult(ids[1], "bbbb2222", "succeeded", "Model built: 9 s."))
    _workspace(tmp_path, "r2", entries[1].package_sha256, "succeeded")
    view.refresh_history(entries, tmp_path)
    rows = _rows(view)
    assert "built " in rows[1] and rows[2].endswith("cancelled")
    assert view.status.text() == "Model built: 9 s." and not view.cancel_button.isEnabled()


def test_interrupted_only_when_no_job_owns_the_workspace(view, tmp_path) -> None:
    entries = [_entry("aaaa1111"), _entry("bbbb2222"), _entry("cccc3333")]
    _workspace(tmp_path, "r1", entries[0].package_sha256, "active")  # app restarted mid-build
    _workspace(tmp_path, "r2", entries[1].package_sha256, "failed", CRASH)
    view.track("trimmed-job", "aaaa1111")  # no longer in the job history: owns nothing
    view.refresh_history(entries, tmp_path)
    rows = _rows(view)
    assert rows[0].endswith("interrupted")
    assert rows[1].endswith("failed: a build step crashed")
    assert rows[2].endswith("not built yet")


def test_plain_failure_reasons() -> None:
    assert plain_failure(CRASH, "8/8 Texturing the mesh") == "texture step (OpenMVS) crashed"
    assert plain_failure("stage exited -1073741819", "2/8 Matching photos") == (
        "photo matching step (COLMAP) crashed"
    )
    assert plain_failure("stage exited 1", "6/8 Building the mesh") == (
        "mesh step (OpenMVS) stopped with error code 1"
    )
    assert plain_failure("stage timed out after 3600 s") == (
        "a build step took too long and was stopped"
    )
    assert plain_failure("BuildModelError: imported package changed since import") == (
        "imported package changed since import"
    )
    assert plain_failure("") == "unknown reason"
    try:
        i18n.set_language("tr")
        assert plain_failure(CRASH, "8/8 Texturing the mesh") == "doku adımı (OpenMVS) çöktü"
    finally:
        i18n.set_language("en")


def test_parts_count_phone_roles_of_scans_imported_here(tmp_path) -> None:
    body, flipped, legacy, foreign = (
        _entry("body1111", "body"),
        _entry("flip2222", "assembled_flipped"),
        _entry("legacy33"),  # manifest omits part_role: assembled
        _entry("foreign4", "closure"),  # in the shared inbox, never imported here
    )
    entries = [body, flipped, legacy, foreign]
    imported = {body.package_sha256, flipped.package_sha256, legacy.package_sha256}
    text = parts_summary_text(entries, {body.package_sha256: "body"}, imported)
    assert "Body: upright present, upside down missing, interior missing" in text
    assert "Assembled: upright present (from phone), upside down present (from phone)" in text
    assert "Closure: upright missing, upside down missing" in text
    try:
        i18n.set_language("tr")
        assert "(telefondan)" in parts_summary_text(entries, {}, imported)
    finally:
        i18n.set_language("en")


def test_queued_scan_counts_from_its_raw_project_copy(view, tmp_path) -> None:
    flip = _entry("flip2222", "assembled_flipped")
    raw = tmp_path / "raw" / "captures"
    raw.mkdir(parents=True)
    (raw / f"{flip.package_sha256}.packscan").write_bytes(b"queued, not built yet")
    view.refresh_history([flip, _entry("foreign4", "closure")], tmp_path)
    parts = view.parts_label.text()
    assert "Assembled: upright missing, upside down present (from phone)" in parts
    assert "Closure: upright missing, upside down missing" in parts
