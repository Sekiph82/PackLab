"""PL-0489 Merge interior on Body in the Scene dock, on SYNTHETIC parts (no metric claim)."""

from __future__ import annotations

import threading

import numpy as np
import pytest

pytest.importorskip("open3d")

from tests.core.test_interior_merge import _cyl, _disc, interior_scan, outer_scan  # noqa: E402
from tests.studio.test_closure_placement import _scan  # noqa: E402
from tests.studio.test_project_parts import _build, _entry, _panel, _pump  # noqa: E402

from packlab_studio.app import create_application  # noqa: E402
from packlab_studio.jobs import JobManager, JobState  # noqa: E402
from packlab_studio.project import ProjectManager  # noqa: E402


@pytest.fixture
def app():
    return create_application(["packlab-interior-merge-test"])


@pytest.fixture
def project(tmp_path):
    manager = ProjectManager(job_manager=JobManager())
    manager.new_project(tmp_path / "jar", "Jar")
    return manager


def _interior(rng, depth=60.0, r=40.0):
    """Steep rings see the outer wall on the near side down to the mat, plus the inside."""
    return np.r_[interior_scan(rng, depth, r=r), _cyl(rng, r, 0, 90, d=0.3)]


def _entries(root, rng, body=None, interior=None):
    body = outer_scan(rng) if body is None else body
    entries = [_entry(_build(root, "b-up", _scan(rng, body)), "body")]
    if interior is not None:
        entries.append(_entry(_build(root, "b-in", _scan(rng, interior)), "body_interior"))
    return entries


def _merge(app, panel) -> str:
    outcomes: list[str] = []
    panel.interior_finished.connect(outcomes.append)
    panel.tree.setCurrentItem(panel.items["body"])
    assert not panel.interior_button.isHidden() and panel.interior_button.isEnabled()
    panel.merge_interior()
    _pump(app, lambda: outcomes, timeout=180)
    return outcomes[0]


def test_merge_interior_persists_coverage_and_reopens(app, project) -> None:
    rng = np.random.default_rng(21)
    root = project.layout.root
    entries = _entries(root, rng, interior=_interior(rng))
    panel = _panel(project, entries)
    body_cloud = panel.states["body"].cloud
    assert _merge(app, panel) == "merged", project.interior_merge()
    record = project.interior_merge()
    assert record["status"] == "merged" and record["metric_status"] == "METRIC_UNVERIFIED"
    assert record["unscanned_depth_filled"] is False
    assert record["body_design_model_affected"] is False
    assert record["sources"]["interior"]["role"] == "body_interior"
    assert record["sources"]["interior"]["scale_source"] == "synthetic_known_mm"
    assert record["deepest_covered_mm"] == pytest.approx(60.0, abs=3.0)
    assert record["missing"] and record["missing"][-1][1] == pytest.approx(100.0, abs=1.5)
    assert record["point_counts"]["interior"] > 0
    status, _record, merged = panel.interior
    assert status == "merged" and merged.name.startswith("body-interior-")
    assert panel.selected_paths() == (merged,)  # viewer shows body + scanned interior
    assert panel.selected_cloud() == body_cloud  # Measure & Design keeps the body cloud
    text = panel.details.text()
    assert "Interior scanned to" in text and "Not scanned (not filled)" in text

    reopened = ProjectManager(job_manager=JobManager())
    reopened.open_project(root)
    again = _panel(reopened, entries)
    assert again.interior[0] == "merged" and again.interior[2] == merged
    merged.write_bytes(b"ply\n")  # tampered merged cloud is never shown as merged
    again.refresh()
    assert again.interior[0] == "stale"


def test_rim_mismatch_refused_and_shown(app, project) -> None:
    rng = np.random.default_rng(22)
    root = project.layout.root
    panel = _panel(project, _entries(root, rng, interior=_interior(rng, r=46.0)))
    assert _merge(app, panel) == "refused"
    record = project.interior_merge()
    assert record["codes"] == ["rim_mismatch"] and record["artifact_path"] is None
    assert panel.interior[0] == "refused"
    assert "Interior merge refused" in panel.details.text()
    assert not list((root / "derived" / "parts").glob("body-interior-*.ply"))


def test_narrow_neck_reports_fallback(app, project) -> None:
    rng = np.random.default_rng(23)
    bottle = np.concatenate(
        [
            _cyl(rng, 35, 0, 150),
            _disc(rng, 11, 35, 160),
            _cyl(rng, 11, 160, 180),
            _disc(rng, 9.5, 11, 180, d=4.0),
        ]
    )
    panel = _panel(project, _entries(project.layout.root, rng, bottle, bottle))
    assert _merge(app, panel) == "refused"
    record = project.interior_merge()
    assert record["codes"] == ["interior_not_reachable"] and "PL-0488" in record["reason"]


def test_no_interior_scan_hides_the_button(app, project) -> None:
    rng = np.random.default_rng(24)
    panel = _panel(project, _entries(project.layout.root, rng))
    panel.tree.setCurrentItem(panel.items["body"])
    assert panel.interior_button.isHidden()
    assert panel.merge_interior() is None and project.interior_merge() is None


def test_cancel_merge_discards_the_result(app, project) -> None:
    rng = np.random.default_rng(25)
    entered, release = threading.Event(), threading.Event()

    def slow(*_parts):
        entered.set()
        release.wait(10)
        raise AssertionError("result must be discarded")

    panel = _panel(
        project, _entries(project.layout.root, rng, interior=_interior(rng)), interior_merger=slow
    )
    panel.tree.setCurrentItem(panel.items["body"])
    job_id = panel.merge_interior()
    _pump(app, entered.is_set, timeout=120)
    assert panel.cancel_button.isEnabled() and not panel.interior_button.isEnabled()
    panel.cancel("body")
    release.set()
    _pump(app, lambda: project.job_manager.get(job_id).state is JobState.CANCELLED)
    assert project.interior_merge() is None


def test_remerge_removes_the_replaced_artifact_and_shows_the_floor(app, project) -> None:
    from dataclasses import replace

    from packlab_core.interior_merge import merge_interior

    rng = np.random.default_rng(26)
    root = project.layout.root
    calls: list[int] = []

    def merger(body, interior):
        result = merge_interior(body, interior)
        calls.append(1)
        return replace(result, points=result.points + 0.001 * len(calls))  # new content

    floor_scan = np.r_[interior_scan(rng, 97.0, floor=True), _cyl(rng, 40.0, 0, 90, d=0.3)]
    panel = _panel(project, _entries(root, rng, interior=floor_scan), interior_merger=merger)
    assert _merge(app, panel) == "merged"
    first = panel.interior[2]
    record = project.interior_merge()
    assert record["floor_depth_mm"] == pytest.approx(97.0, abs=1.0)
    assert record["missing"] == [] and record["bands"][-1]["kind"] == "base"
    assert "Inner floor at" in panel.details.text()
    assert "Not scanned" not in panel.details.text()
    assert _merge(app, panel) == "merged"
    second = panel.interior[2]
    assert second != first and second.exists() and not first.exists()
