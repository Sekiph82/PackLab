"""PL-0484 Place closure on body in the Scene dock, on SYNTHETIC parts (no metric claim)."""

from __future__ import annotations

import threading

import numpy as np
import pytest

pytest.importorskip("open3d")

from tests.core.test_part_placement import assembled, body, lid  # noqa: E402
from tests.studio.test_project_parts import _build, _entry, _panel, _pump  # noqa: E402

from packlab_studio.app import create_application  # noqa: E402
from packlab_studio.jobs import JobManager, JobState  # noqa: E402
from packlab_studio.project import ProjectManager  # noqa: E402


@pytest.fixture
def app():
    return create_application(["packlab-closure-placement-test"])


@pytest.fixture
def project(tmp_path):
    manager = ProjectManager(job_manager=JobManager())
    manager.new_project(tmp_path / "jar", "Jar")
    return manager


def _scan(rng, obj: np.ndarray, flipped: bool = False) -> np.ndarray:
    """One scan on the A4 mat: object at a random yaw / offset, mat plane, 0.15 mm noise."""
    if flipped:
        obj = obj * [1, -1, -1] + [0, 0, obj[:, 2].max()]
    yaw = rng.uniform(0, 2 * np.pi)
    c, s = np.cos(yaw), np.sin(yaw)
    obj = obj @ np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]]).T + [*rng.uniform(-30, 30, 2), 0]
    mat = np.c_[rng.uniform(-148, 148, 18000), rng.uniform(-105, 105, 18000), np.zeros(18000)]
    points = np.r_[obj, mat]
    return points + rng.normal(0, 0.15, points.shape)


def _entries(root, rng, lid_radius=37.5, combined_body=True, closure=True):
    entries = [
        _entry(_build(root, "a-up", _scan(rng, assembled(rng))), "assembled"),
        _entry(_build(root, "b-up", _scan(rng, body(rng))), "body"),
    ]
    if combined_body:
        entries.append(_entry(_build(root, "b-flip", _scan(rng, body(rng), True)), "body_flipped"))
    if closure:
        entries.append(_entry(_build(root, "c-up", _scan(rng, lid(rng, lid_radius))), "closure"))
    return entries


def _place(app, panel) -> str:
    outcomes: list[str] = []
    panel.placement_finished.connect(outcomes.append)
    panel.tree.setCurrentItem(panel.items["assembled"])
    assert panel.place_button.isEnabled()
    panel.place()
    _pump(app, lambda: outcomes, timeout=180)
    return outcomes[0]


def test_place_closure_on_combined_body_persists_and_reopens(app, project) -> None:
    rng = np.random.default_rng(11)
    root = project.layout.root
    entries = _entries(root, rng)
    from packlab_core.part_placement import place_closure_on_body

    threads = []

    def placer(*parts):
        threads.append(threading.current_thread())
        return place_closure_on_body(*parts)

    panel = _panel(project, entries, placer=placer)
    combined: list[str] = []
    panel.combine_finished.connect(lambda _part, outcome: combined.append(outcome))
    panel.combine("body")
    _pump(app, lambda: combined, timeout=180)
    assert combined == ["combined"], project.part_merges()

    assert _place(app, panel) == "placed", project.part_placement()
    assert threads and threads[0] is not threading.main_thread()
    record = project.part_placement()
    assert record["status"] == "placed" and record["metric_status"] == "METRIC_UNVERIFIED"
    assert record["sources"]["body"]["status"] == "combined"
    assert record["sources"]["closure"]["scale_source"] == "synthetic_known_mm"
    graph = record["graph"]
    assert record["graph_revision_id"] == graph["revision_id"]
    assert [c["role"] for c in graph["components"]] == ["container", "closure"]
    assert graph["diagnostics"]["pair"]["status"] in ("CLEARANCE", "NEAR_CLEARANCE")
    assert graph["relationships"][0]["engaged_depth_mm"] == pytest.approx(13.0, abs=1.5)
    assert graph["mold_use_authorized"] is False
    status, _record, placed = panel.placement
    assert status == "placed" and [p.name.split("-placed-")[0] for p in placed] == [
        "body",
        "closure",
    ]
    assert panel.selected_paths() == (panel.states["assembled"].cloud, *placed)
    assert "Closure placed on body" in panel.details.text()
    # The placed closure sits on top of the placed body (lid top = assembled top, 82 mm).
    import open3d as o3d

    lid_z = np.asarray(o3d.io.read_point_cloud(str(placed[1])).points)[:, 2]
    body_z = np.asarray(o3d.io.read_point_cloud(str(placed[0])).points)[:, 2]
    assert np.percentile(lid_z, 99.5) == pytest.approx(82.0, abs=1.0)
    assert np.percentile(body_z, 99.5) == pytest.approx(80.0, abs=1.0)

    # Per-part visibility still applies to the placed parts.
    project.set_part_view("assembled", ["closure"])
    panel.refresh()
    assert panel.selected_paths() == (panel.states["assembled"].cloud, placed[0])

    reopened = ProjectManager(job_manager=JobManager())
    reopened.open_project(root)
    again = _panel(reopened, entries)
    assert again.placement[0] == "placed" and again.placement[2] == placed
    placed[1].write_bytes(b"ply\n")  # tampered placed cloud is never shown as placed
    again.refresh()
    assert again.placement[0] == "stale" and "place it again" in again.details.text()


def test_wrong_lid_is_refused_and_shown(app, project) -> None:
    rng = np.random.default_rng(12)
    root = project.layout.root
    panel = _panel(project, _entries(root, rng, lid_radius=43.0, combined_body=False))
    assert _place(app, panel) == "refused"
    record = project.part_placement()
    assert record["status"] == "refused" and record["artifacts"] == {}
    assert "diameter_mismatch" in record["codes"] or "coverage" in record["codes"]
    assert panel.placement[0] == "refused"
    assert "Closure placement refused" in panel.details.text()
    assert not list((root / "derived" / "parts").glob("*-placed-*.ply"))


def test_missing_closure_cannot_be_placed(app, project) -> None:
    rng = np.random.default_rng(13)
    panel = _panel(project, _entries(project.layout.root, rng, combined_body=False, closure=False))
    panel.tree.setCurrentItem(panel.items["assembled"])
    assert not panel.place_button.isEnabled()
    assert panel.place() is None and project.part_placement() is None


def test_placement_of_flipped_only_part_is_refused(app, project) -> None:
    rng = np.random.default_rng(14)
    root = project.layout.root
    entries = [
        _entry(_build(root, "a-up", _scan(rng, assembled(rng))), "assembled"),
        _entry(_build(root, "b-flip", _scan(rng, body(rng), True)), "body_flipped"),
        _entry(_build(root, "c-up", _scan(rng, lid(rng))), "closure"),
    ]
    panel = _panel(project, entries)
    assert _place(app, panel) == "refused"
    record = project.part_placement()
    assert record["codes"] == ["part_missing"] and "upside-down" in record["reason"]


def test_cancel_placement_discards_the_result(app, project) -> None:
    rng = np.random.default_rng(15)
    entered, release = threading.Event(), threading.Event()

    def slow(*_parts):
        entered.set()
        release.wait(10)
        raise AssertionError("result must be discarded")

    entries = _entries(project.layout.root, rng, combined_body=False)
    panel = _panel(project, entries, placer=slow)
    panel.tree.setCurrentItem(panel.items["assembled"])
    job_id = panel.place()
    _pump(app, entered.is_set, timeout=120)
    assert panel.cancel_button.isEnabled() and not panel.place_button.isEnabled()
    panel.cancel("assembled")
    release.set()
    _pump(app, lambda: project.job_manager.get(job_id).state is JobState.CANCELLED)
    assert project.part_placement() is None
