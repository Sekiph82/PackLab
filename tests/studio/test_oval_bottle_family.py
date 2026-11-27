"""PL-0492 oval / flat bottle Design Model through the real StudioMainWindow offscreen.

The Scan Masters are synthetic meshes (exact superellipse walls of known size); passing
proves the fit -> confirm -> edit -> save -> labels -> reopen -> STEP/STL wiring and
lineage, not physical accuracy (METRIC_UNVERIFIED, DEFERRED_OWNER_VALIDATION).
"""

from __future__ import annotations

import hashlib
import json
import math

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

    view.create_button.click()  # unconfirmed: shows the detected class, creates nothing
    assert view.design is None
    assert "detected OVAL: 60.0 x 34.0 x 160.0 mm_unverified" in view.status.text()
    view.confirm_shape.setChecked(True)
    view.create_button.click()
    design = view.design
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
    for kind in (LabelZoneKind.FRONT, LabelZoneKind.BACK):
        entry = workbench.add_label_zone(workbench.suggest_label_zone(kind))
        width, height = entry.size_mm
        assert width > 5.0 and height > 50.0  # on the flat body panel facing +/-Y
    with pytest.raises(Exception, match="cylindrical"):
        workbench.suggest_label_zone(LabelZoneKind.WRAP)
    svg, _export_record = workbench.export_dieline_svg(workbench.labels[0], tmp_path)
    assert svg.read_bytes().lstrip().startswith(b"<")

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
