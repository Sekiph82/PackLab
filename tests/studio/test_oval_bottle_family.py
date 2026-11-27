"""PL-0492 oval / flat bottle Design Model through the real StudioMainWindow offscreen.

The Scan Masters are synthetic meshes (exact superellipse walls of known size); passing
proves the fit -> confirm -> edit -> save -> labels -> reopen -> STEP/STL wiring and
lineage, not physical accuracy (METRIC_UNVERIFIED, DEFERRED_OWNER_VALIDATION).
"""

from __future__ import annotations

import hashlib
import json
import math

import numpy as np
import pytest

pytest.importorskip("cv2")
pytest.importorskip("open3d")

from tests.studio.test_package_families import (  # noqa: E402,F401
    _choose,
    _export,
    _families,
    window,
)

from packlab_core.cad_validation import validate_cad_brep  # noqa: E402
from packlab_core.geometry_adapter import TriangleMeshData  # noqa: E402
from packlab_core.label_zone import LabelZoneKind  # noqa: E402
from packlab_core.scan_master import ScanMasterRevision, mesh_sha256  # noqa: E402
from packlab_studio import package_families as pf  # noqa: E402
from packlab_studio.navigation import Route  # noqa: E402


def _bottle_scan_master(
    project_id: str, a: float, b: float, n: float, scale_state: str = "metric-unverified"
) -> ScanMasterRevision:
    """Superellipse body (half-axes a along y, b along x: long side on the mat's Y) to
    112 mm, shoulder to 136 mm, round 24 mm neck to 160 mm; rings every 2 mm."""
    count, levels = 96, 81
    vertices = []
    for level in range(levels):
        z = 2.0 * level
        f = z / 160.0
        if f < 0.7:
            aa, bb, nn = a, b, n
        elif f < 0.85:
            t = (f - 0.7) / 0.15
            aa, bb, nn = a + (12 - a) * t, b + (12 - b) * t, n + (2 - n) * t
        else:
            aa = bb = 12.0
            nn = 2.0
        for i in range(count):
            t = math.tau * i / count
            c, s = math.cos(t), math.sin(t)
            vertices.append(
                (
                    bb * math.copysign(abs(s) ** (2 / nn), s),
                    aa * math.copysign(abs(c) ** (2 / nn), c),
                    z,
                )
            )
    faces = []
    for level in range(levels - 1):
        for i in range(count):
            p, q = level * count + i, level * count + (i + 1) % count
            faces.extend(((p, q, q + count), (p, q + count, p + count)))
    mesh = TriangleMeshData(tuple(vertices), tuple(faces))
    revision_id = f"scan-master:{hashlib.sha256(f'oval-{a}-{b}-{n}'.encode()).hexdigest()}"
    return ScanMasterRevision(
        revision_id,
        project_id,
        mesh,
        {
            "scan_master_revision_id": revision_id,
            "project_id": project_id,
            "authority_class": "SCAN_MASTER",
            "raw_capture_revision_id": "capture-r1",
            "raw_capture_sha256": "c" * 64,
            "reconstruction_revision_id": "reconstruction-r1",
            "parent_object_geometry_revision_id": "object-r1",
            "scale_provenance_id": "scale-r1",
            "scale_state": scale_state,
            "output_geometry_sha256": mesh_sha256(mesh),
            "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
            "mold_use_authorized": False,
            "known_limitations": ["synthetic test revision"],
            "coverage_gaps": [],
            "promotion_actor": "operator-test",
            "promotion_reason": "Synthetic oval bottle.",
            "hole_report": {"parent_revision_id": "cleanup-r1"},
        },
    )


def test_oval_bottle_fit_confirm_edit_save_labels_reopen_export(window, tmp_path) -> None:  # noqa: F811
    window.new_project(tmp_path / "project", "Oval bottle")
    manager = window.project_manager
    scan = _bottle_scan_master(manager.current.project_id, 30.0, 17.0, 2.0)
    manager.persist_scan_master_revision(scan, expected_revision=manager.current.revision)
    view = _families(window)
    _choose(view, "oval_bottle", "Fit to the selected Scan Master", "captured")
    assert view.confirm_shape.isVisibleTo(view) and not view.confirm_shape.isChecked()

    view.create_button.click()  # the fit runs on a worker thread (UI stays responsive)
    assert view.busy.isVisibleTo(view) and view.cancel_fit_button.isVisibleTo(view)
    view.wait_for_fit(60)
    assert view.design is None  # unconfirmed: shows the detected class, creates nothing
    jobs = [job for job in window.job_manager.jobs() if job.job_type == "oval-section-fit"]
    assert jobs and jobs[-1].state.value == "succeeded"
    assert "detected OVAL: 60.0 x 34.0 x 160.0 mm_unverified" in view.status.text()
    view.confirm_shape.setChecked(True)
    view.create_button.click()  # reuses the fit the owner saw: no second fit job
    design = view.design
    assert len([j for j in window.job_manager.jobs() if j.job_type == "oval-section-fit"]) == 1
    assert design is not None, view.status.text()
    assert design.model.fitted_to_scan_master_revision_id == scan.revision_id
    assert design.model.physical_accuracy_validation_status == "DEFERRED_OWNER_VALIDATION"
    assert design.model.mold_use_authorized is False
    dims = design.overall_dimensions()  # long side rotated onto the design X axis
    assert dims["width"] == pytest.approx(60.0, abs=0.1)
    assert dims["depth"] == pytest.approx(34.0, abs=0.1)
    assert dims["height"] == pytest.approx(160.0, abs=0.1)
    evidence = next(
        item.as_dict()["value"]
        for item in design.model.parameters
        if item.parameter_id == "oval_section_fit_evidence"
    )
    assert evidence["classification"] == "OVAL"
    assert evidence["owner_confirmed_classification"]["confirmed"] is True
    assert evidence["orientation_deg"] == pytest.approx(90.0, abs=1.0)
    assert {name for name, _z0, _z1 in evidence["zones"]} >= {"body", "shoulder", "neck"}
    report = validate_cad_brep(design.part("body").representation)
    assert report.valid_closed_solid and report.solid_count == 1, report.failure_diagnostics

    view.spins["width"].setValue(64.0)
    view.spins["neck_diameter"].setValue(26.0)
    view.apply_button.click()
    edited = view.design
    assert edited.model.previous_revision_id == design.model.revision_id, view.status.text()
    assert edited.overall_dimensions()["width"] == pytest.approx(64.0, abs=0.1)
    assert edited.overall_dimensions()["depth"] == pytest.approx(34.0, abs=0.1)
    top = edited.part("body").preview.mesh.vertices
    neck = [v for v in top if v[2] > 159.9]
    assert max(v[0] for v in neck) - min(v[0] for v in neck) == pytest.approx(26.0, abs=0.6)

    view.spins["neck_diameter"].setValue(40.0)  # wider than the 34 mm depth
    view.apply_button.click()
    assert "neck diameter must be smaller" in view.status.text()
    assert view.design is edited
    view.spins["neck_diameter"].setValue(26.0)

    view.save_button.click()
    record, document = manager.selected_design_model()
    assert record["revision_id"] == edited.model.revision_id, view.status.text()
    assert record["scan_master_revision_id"] == scan.revision_id
    assert record["parent_kind"] == "CAPTURED_SCAN_MASTER"
    assert document["package_family_workflow"]["oval_section_fit"]["classification"] == "OVAL"

    labels = window.route_stack.views[Route.LABELS]
    labels.use_project_model()
    assert "Opened project Design Model" in labels.status.text(), labels.status.text()
    workbench = labels.workbench
    # Labels follow the curved oval body band (64 x 34 mm after the edit), not only the
    # flat panel: front/back along the side arc facing +/-Y, wrap all the way round.
    side = None
    for kind in (LabelZoneKind.FRONT, LabelZoneKind.BACK):
        entry = workbench.add_label_zone(workbench.suggest_label_zone(kind))
        binding = entry.metric_binding
        assert binding.mapping_mode == "PRISM_PERIMETER_WRAP"
        width, height = entry.size_mm
        assert 40.0 < width < 56.0 and height > 50.0, entry.size_mm
        side = binding.host_width_mm_unverified
        assert 70.0 < side < 85.0  # the -X .. +X side arc, longer than the 64 mm chord
    wrap = workbench.add_label_zone(workbench.suggest_label_zone(LabelZoneKind.WRAP))
    a, b = 32.0, 17.0  # Ramanujan: perimeter of the 64 x 34 ellipse
    h = ((a - b) / (a + b)) ** 2
    perimeter = math.pi * (a + b) * (1 + 3 * h / (10 + math.sqrt(4 - 3 * h)))
    assert wrap.metric_binding.host_width_mm_unverified == pytest.approx(perimeter, rel=0.01)
    assert wrap.metric_binding.host_width_mm_unverified == pytest.approx(2 * side, rel=0.02)
    svg, export = workbench.export_dieline_svg(workbench.labels[0], tmp_path)
    assert svg.read_bytes().lstrip().startswith(b"<")
    front_width = workbench.labels[0].size_mm[0]
    sidecar = json.loads(svg.with_suffix(".json").read_text(encoding="utf-8"))
    assert sidecar["dieline"]["mapping_mode"] == "PRISM_PERIMETER_WRAP"
    assert sidecar["dieline"]["width"] == pytest.approx(front_width)  # mm along the surface
    assert export.width_mm_unverified > front_width

    view.design = None
    view.open_button.click()
    assert view.design is not None and view.design.model == edited.model, view.status.text()
    steps = _export(window, tmp_path, "body", "step")
    assert steps and steps[0].read_bytes().startswith(b"ISO-10303-21")
    stls = _export(window, tmp_path, "body", "stl")
    assert stls and stls[0].stat().st_size > 1000
    assert json.loads(json.dumps(document, default=str))  # persisted record is plain JSON


def test_rounded_rectangle_and_round_scans(window, tmp_path) -> None:  # noqa: F811
    window.new_project(tmp_path / "project", "Shapes")
    project_id = window.project_manager.current.project_id
    square = pf.fit_oval_bottle_on_scan_master(
        _bottle_scan_master(project_id, 30.0, 20.0, 4.0), actor_id="owner", owner_confirmed=True
    )
    assert square.extra["oval_section_fit"]["classification"] == "ROUNDED_RECTANGLE"
    assert square.overall_dimensions()["width"] == pytest.approx(60.0, abs=0.1)
    assert square.overall_dimensions()["depth"] == pytest.approx(40.0, abs=0.1)
    with pytest.raises(pf.PackageFamilyError, match="round_use_revolved_fit"):
        pf.fit_oval_bottle_on_scan_master(
            _bottle_scan_master(project_id, 25.0, 25.0, 2.0),
            actor_id="owner",
            owner_confirmed=True,
        )
    relative = _bottle_scan_master(project_id, 30.0, 17.0, 2.0, scale_state="relative")
    with pytest.raises(pf.PackageFamilyError, match="not scaled to mm"):
        pf.fit_oval_bottle_on_scan_master(relative, actor_id="owner", owner_confirmed=True)


def test_confirm_resets_on_scan_master_change_and_fit_cancels(window, tmp_path) -> None:  # noqa: F811
    window.new_project(tmp_path / "project", "Oval reset")
    manager = window.project_manager
    first = _bottle_scan_master(manager.current.project_id, 30.0, 17.0, 2.0)
    manager.persist_scan_master_revision(first, expected_revision=manager.current.revision)
    view = _families(window)
    _choose(view, "oval_bottle", "Fit to the selected Scan Master", "captured")
    view.create_button.click()
    view.wait_for_fit(60)
    assert "detected OVAL" in view.status.text()
    view.confirm_shape.setChecked(True)  # the owner confirmed the first scan's shape ...
    second = _bottle_scan_master(manager.current.project_id, 30.0, 20.0, 4.0)
    manager.persist_scan_master_revision(second, expected_revision=manager.current.revision)
    assert not view.confirm_shape.isChecked()  # ... not this one
    view.create_button.click()  # a new fit of the new Scan Master; nothing is created
    view.cancel_fit()
    view.wait_for_fit(60)
    assert view.design is None
    assert "cancelled" in view.status.text(), view.status.text()
    fits = [job for job in window.job_manager.jobs() if job.job_type == "oval-section-fit"]
    assert fits[-1].state.value == "cancelled"
    view.create_button.click()
    view.wait_for_fit(60)
    assert "detected ROUNDED_RECTANGLE" in view.status.text(), view.status.text()
    view.confirm_shape.setChecked(True)
    view.create_button.click()
    assert view.design is not None, view.status.text()
    assert view.design.model.fitted_to_scan_master_revision_id == second.revision_id


def test_neck_offset_scales_with_the_body_not_the_neck(window, tmp_path) -> None:  # noqa: F811
    window.new_project(tmp_path / "project", "Neck offset")
    scan = _bottle_scan_master(window.project_manager.current.project_id, 30.0, 17.0, 2.0)
    design = pf.fit_oval_bottle_on_scan_master(scan, actor_id="owner", owner_confirmed=True)
    values = dict(design.parameters)
    values["oval_sections"] = [
        [row[0], row[1] + (4.0 if row[6] == "neck" else 0.0), *row[2:]]
        for row in values["oval_sections"]
    ]
    values["width"] = 2.0 * values["width"]  # body twice as wide, neck diameter unchanged
    loft = pf._oval_spec(values).parts[0]
    top = loft.sections[-1][2]
    xs = [point.x for point in top.points]
    assert (max(xs) + min(xs)) / 2 == pytest.approx(8.0, abs=1e-6)  # offset 4 mm x 2
    assert max(xs) - min(xs) == pytest.approx(24.0, abs=1e-6)  # neck diameter kept


def test_curved_labels_read_left_to_right_in_preview_and_blender(
    window,  # noqa: F811
    tmp_path,
    monkeypatch,
) -> None:
    """Left-half-blue artwork on the curved front and back: seen from outside, the left
    half is on the viewer's left (front: +X, back: -X); Blender uses the same function."""
    from tests.studio.test_label_top_disc import _png

    from packlab_core import blender_scene_package as package
    from packlab_studio.design_workbench import DesignWorkbench, label_preview_points

    window.new_project(tmp_path / "project", "Oval labels")
    scan = _bottle_scan_master(window.project_manager.current.project_id, 31.0, 17.0, 2.0)
    design = pf.fit_oval_bottle_on_scan_master(scan, actor_id="owner", owner_confirmed=True)
    bench = DesignWorkbench()
    bench.open_document(json.dumps(design.as_dict(), default=str).encode())
    for kind, left_x in ((LabelZoneKind.FRONT, 1.0), (LabelZoneKind.BACK, -1.0)):
        entry = bench.add_label_zone(bench.suggest_label_zone(kind))
        assert entry.size_mm[0] == pytest.approx(49.6, abs=1.5)  # ~50 mm along the curve
        bench.import_artwork(entry, _png(200, 100), fit_mode="STRETCH")
        points, colors = label_preview_points(bench.session, entry)
        blue = colors[:, 2] > colors[:, 0]
        assert (np.sign(points[blue, 0]) == left_x).mean() > 0.95, kind
        assert (np.sign(points[~blue, 0]) == -left_x).mean() > 0.95, kind
        facing = 1.0 if kind is LabelZoneKind.FRONT else -1.0
        assert (points[:, 1] * facing > 0).all()  # on the facing side of the curved body
    monkeypatch.setenv("PACKLAB_BUILD_REVISION", "a" * 40)
    fake = tmp_path / "blender.exe"
    fake.write_bytes(b"not run")
    job = bench.prepare_mockup(tmp_path, executable=fake)
    overlays = job.package.manifest()["body"]["scene"]["overlays"]
    assert [item["mapping_mode"] for item in overlays] == ["PRISM_PERIMETER_WRAP"] * 2
    for overlay in overlays:
        assert package.artwork_viewer_orientation(overlay) == (True, True)
