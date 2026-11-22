"""PL-0487: labels on Closure, Body and Assembled, traceable to each part's Design Model.

Synthetic nominal Design Models only (body 50 x 85 mm, closure 15 x 90 mm, mm_unverified);
nothing here is a physical measurement.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import numpy as np
import pytest
from PySide6.QtCore import QSettings

from packlab_studio import i18n, labels_view
from packlab_studio.app import create_application
from packlab_studio.design_workbench import (
    label_preview_points,
    load_design_model_session,
    nominal_jar_design_document,
)
from packlab_studio.navigation import Route
from packlab_studio.shell import StudioMainWindow

SVG = (
    b'<svg xmlns="http://www.w3.org/2000/svg" width="200" height="40" viewBox="0 0 200 40">'
    b'<rect width="200" height="40" fill="#d22"/><circle cx="20" cy="20" r="15" fill="#22d"/>'
    b"</svg>"
)
SEAT_MM = 47.0  # synthetic closure-on-body seat height


@pytest.fixture
def app(monkeypatch, tmp_path):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    application = create_application(["packlab-labels-per-part"])
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    QSettings.setPath(
        QSettings.Format.IniFormat, QSettings.Scope.UserScope, str(tmp_path / "settings")
    )
    return application


def _window(tmp_path: Path, name: str = "a") -> StudioMainWindow:
    return StudioMainWindow(
        packaging_library_root=tmp_path / f"library-{name}",
        diagnostics_root=tmp_path / f"diag-{name}",
    )


def _save_part_model(manager, part: str, *, height: float, diameter: float) -> str:
    """Standalone (ADR-0005) Measure & Design-shaped revision saved as ``part``'s model."""
    document = nominal_jar_design_document(
        height_mm=height,
        diameter_mm=diameter,
        project_id=manager.current.project_id,
        created_at_utc="2026-11-22T00:00:00Z",
    )
    session = load_design_model_session(document)
    record = {
        "contract": "packlab.studio-design-model-revision.v1",
        "design_model_revision_id": session.model.revision_id,
        "revision_history": [session.model.revision_id],
        "overall_dimensions_mm_unverified": {"height": height, "diameter": diameter},
        "fitted_from_scan": {"height": height, "diameter": diameter},
        "model": session.model.as_dict(),
        "revolved_fit": {
            "profile": session.profile.as_dict(),
            "operation": session.operation.as_dict(),
        },
        "design_document": document.decode("utf-8"),
        "notes": [],
        "scan_master_replaced": False,
        "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
        "mold_use_authorized": False,
    }
    saved = manager.persist_design_model_revision(
        record, expected_revision=manager.current.revision, part=part
    )
    assert saved["part"] == part
    return session.model.revision_id


YAW_DEG = 37.0
BODY_AXIS = (12.0, -7.0)  # each part's axis in its own scan mat frame (mm)
CLOSURE_AXIS = (-20.0, 5.0)


def _translate(x: float, y: float, z: float = 0.0) -> np.ndarray:
    matrix = np.eye(4)
    matrix[:3, 3] = (x, y, z)
    return matrix


def _yaw(degrees: float) -> np.ndarray:
    c, s = np.cos(np.radians(degrees)), np.sin(np.radians(degrees))
    matrix = np.eye(4)
    matrix[:2, :2] = ((c, -s), (s, c))
    return matrix


def _frames(manager, monkeypatch, *, closure_sha: str = "c" * 64) -> None:
    """Measure & Design frames (scan mat frame -> Design Model frame) of both parts."""
    frames = {
        "body": {
            "source_cloud_sha256": "b" * 64,
            "source_frame": "part_combine_mat_frame_mm",
            "source_to_scan_master": _translate(-BODY_AXIS[0], -BODY_AXIS[1]).ravel().tolist(),
        },
        "closure": {
            "source_cloud_sha256": closure_sha,
            "source_frame": "part_combine_mat_frame_mm",
            "source_to_scan_master": _translate(-CLOSURE_AXIS[0], -CLOSURE_AXIS[1])
            .ravel()
            .tolist(),
        },
    }
    monkeypatch.setattr(manager, "part_design_frame", lambda part: frames[part])


def _placement(seat: float = SEAT_MM):
    """Closure scan seated on the body scan: its axis onto the body axis, turned by YAW."""
    matrix = (
        _translate(BODY_AXIS[0], BODY_AXIS[1], seat)
        @ _yaw(YAW_DEG)
        @ _translate(-CLOSURE_AXIS[0], -CLOSURE_AXIS[1])
    )
    record = {
        "status": "placed",
        "sources": {
            part: {"cloud_sha256": sha * 64, "frame": "part_combine_mat_frame_mm"}
            for part, sha in (("assembled", "a"), ("body", "b"), ("closure", "c"))
        },
        "graph": {
            "revision_id": "scan-assembly-graph:" + "a" * 64,
            "relationships": [{"closure_on_body": matrix.ravel().tolist()}],
        },
    }
    return lambda: ("placed", record, ())


def _add_wrap(labels, variant: str, *, v_min: float = 0.1, v_max: float = 0.9) -> None:
    labels.kind.setCurrentIndex(labels.kind.findData("wrap"))
    labels.boundary["v_min"].setValue(v_min)
    labels.boundary["v_max"].setValue(v_max)
    labels.variant.setText(variant)
    labels.add_zone_button.click()
    assert f"Added {variant}" in labels.status.text(), labels.status.text()


def _add_top(labels, variant: str) -> None:
    labels.kind.setCurrentIndex(labels.kind.findData("top"))
    assert labels.disc_row.isEnabled() and not labels.boundary["u_min"].isEnabled()
    labels.disc_outer.setValue(40.0)
    labels.disc_inner.setValue(10.0)
    labels.disc_rotation.setValue(30.0)
    labels.variant.setText(variant)
    labels.add_zone_button.click()
    assert f"Added {variant}" in labels.status.text(), labels.status.text()


def _project(app, tmp_path):
    window = _window(tmp_path)
    window.new_project(tmp_path / "jar", "Jar")
    manager = window.project_manager
    body = _save_part_model(manager, "body", height=50.0, diameter=85.0)
    closure = _save_part_model(manager, "closure", height=15.0, diameter=90.0)
    labels = window.route_stack.views[Route.LABELS]
    artwork = tmp_path / "art.svg"
    artwork.write_bytes(SVG)
    labels.choose_artwork_path = lambda: str(artwork)
    return window, manager, labels, body, closure


def test_each_part_has_its_own_design_model_labels_and_reopens(app, tmp_path) -> None:
    window, manager, labels, body, closure = _project(app, tmp_path)
    try:
        assert manager.part_design_model("body")[0]["revision_id"] == body
        assert manager.part_design_model("closure")[0]["revision_id"] == closure
        assert manager.selected_design_model()[0]["revision_id"] == closure  # last save

        labels.show_part("body")
        assert labels.part_selector.currentData() == "body"
        assert labels.workbench.session.model.revision_id == body
        assert "height 50.0 mm" in labels.model_summary.text()
        assert [labels.kind.itemData(i) for i in range(labels.kind.count())] == [
            "wrap",
            "front",
            "back",
        ]
        _add_wrap(labels, "body-wrap")
        labels.import_button.click()
        assert "Saved in the project" in labels.status.text(), labels.status.text()
        document = manager.part_labels("body")
        assert document["design_model_revision_id"] == body
        assert document["contract"] == "packlab.studio-part-labels.v1"
        (label,) = document["labels"]
        assert label["kind"] == "wrap" and label["artwork"]["media_type"] == "image/svg+xml"
        assert (manager.layout.root / label["artwork"]["path"]).read_bytes() == SVG

        labels.show_part("closure")
        assert labels.workbench.session.model.revision_id == closure
        assert [labels.kind.itemData(i) for i in range(labels.kind.count())] == ["wrap", "top"]
        assert manager.part_labels("closure") is None
        _add_top(labels, "top-print")
        labels.import_button.click()
        assert labels.workbench.labels[0].size_mm == pytest.approx((80.0, 80.0))
        _add_wrap(labels, "skirt")
        width, height = labels.workbench.labels[1].size_mm
        assert height <= 15.0 and width == pytest.approx(np.pi * 90.0, rel=1e-3)
        document = manager.part_labels("closure")
        assert document["design_model_revision_id"] == closure
        top = document["labels"][0]
        assert top["kind"] == "top" and top["artwork"] is not None
        assert top["disc"] == {
            "outer_radius_mm_unverified": 40.0,
            "inner_radius_mm_unverified": 10.0,
            "rotation_degrees": 30.0,
        }

        labels.show_part("body")  # switching back restores the body labels from the project
        assert [entry.variant_id for entry in labels.workbench.labels] == ["body-wrap"]
        assert labels.workbench.labels[0].artwork.content == SVG

        other = tmp_path / "other.packlab-design.json"  # not the body's Design Model
        other.write_bytes(nominal_jar_design_document(height_mm=40.0, diameter_mm=70.0))
        labels.choose_design_model_path = lambda: str(other)
        labels.open_button.click()
        _add_wrap(labels, "elsewhere")
        assert "Not saved in the project" in labels.status.text()
        assert len(manager.part_labels("body")["labels"]) == 1
    finally:
        window.close()
        app.processEvents()

    reopened = _window(tmp_path, "b")
    try:
        reopened.open_project(tmp_path / "jar")
        view = reopened.route_stack.views[Route.LABELS]
        view.show_part("closure")
        assert [entry.variant_id for entry in view.workbench.labels] == ["top-print", "skirt"]
        assert "2 label(s) restored" in view.status.text(), view.status.text()
        restored = dict(view.workbench.labels[0].metric_binding.mapping_parameters)
        assert restored["label_outer_radius_mm_unverified"] == pytest.approx(40.0)
        assert restored["label_inner_radius_mm_unverified"] == pytest.approx(10.0)
        assert restored["rotation_degrees"] == pytest.approx(30.0)
        view.show_part(None)  # project mode: the project's current Design Model again
        assert view.workbench.session.model.revision_id == closure
        assert view.workbench.labels == []
    finally:
        reopened.close()
        app.processEvents()


def test_labels_go_stale_when_the_part_design_model_changes(app, tmp_path) -> None:
    window, manager, labels, body, _closure = _project(app, tmp_path)
    try:
        labels.show_part("body")
        _add_wrap(labels, "body-wrap")
        newer = _save_part_model(manager, "body", height=60.0, diameter=85.0)
        assert newer != body
        # The project listener reopened the body on its new revision; labels are stale.
        assert labels.workbench.session.model.revision_id == newer
        assert labels.workbench.labels == []
        assert "STALE" in labels.status.text() and body[:32] in labels.status.text()
        assert labels.reapply_button.isEnabled()
        assert manager.part_labels("body")["design_model_revision_id"] == body  # kept

        labels.reapply_button.click()
        assert "1 label(s) re-applied" in labels.status.text(), labels.status.text()
        assert manager.part_labels("body")["design_model_revision_id"] == newer
        assert not labels.reapply_button.isVisible()
        assert labels.workbench.labels[0].placement.label_zone.source_design_model_revision_id == (
            newer
        )
    finally:
        window.close()
        app.processEvents()


def test_assembled_shows_both_parts_labels_with_the_placement(app, tmp_path, monkeypatch):
    window, manager, labels, _body, _closure = _project(app, tmp_path)
    try:
        labels.show_part("assembled")
        assert "closure placed on the body" in labels.status.text()  # no placement yet
        assert labels.assembled_geometry == []

        labels.show_part("body")
        _add_wrap(labels, "body-wrap")
        labels.import_button.click()
        labels.show_part("closure")
        _add_wrap(labels, "skirt")
        labels.import_button.click()
        _add_top(labels, "top-print")
        labels.import_button.click()

        labels.placement_provider = _placement()
        labels.show_part("assembled")
        assert "no recorded scan frame" in labels.status.text()  # standalone models
        _frames(manager, monkeypatch, closure_sha="d" * 64)
        labels.show_part("body")
        labels.show_part("assembled")
        assert "fitted to another cloud" in labels.status.text()
        _frames(manager, monkeypatch)
        labels.show_part("body")
        labels.show_part("assembled")
        assert labels.assembled_viewer.isVisibleTo(labels)
        assert not labels.render_button.isEnabled()
        assert "one Design Model at a time" in labels.status.text()
        shown = {object_id: geometry for object_id, _kind, geometry in labels.assembled_geometry}
        assert set(shown) == {
            "body",
            "closure",
            "body-label-0",
            "closure-label-0",
            "closure-label-1",
        }
        top = np.asarray(shown["closure-label-1"].points)  # closure top print, seated
        assert np.allclose(top[:, 1], SEAT_MM + 15.0 + 0.2)
        top_radius = np.hypot(top[:, 0], top[:, 2])
        assert top_radius.max() <= 40.0 + 1e-6 and top_radius.min() >= 10.0 - 1e-6
        # The closure Design Model, composed through both scan frames and the placement,
        # lands on the body axis (offsets cancel) turned by the placement's yaw.
        workbench, _note = labels._part_workbench("closure")
        unplaced, _colors = label_preview_points(workbench.session, workbench.labels[1])
        expected = unplaced @ _yaw(YAW_DEG)[:3, :3].T + (0.0, 0.0, SEAT_MM)
        assert np.allclose(top, [(x, z, -y) for x, y, z in expected])
        # viewer is y-up: y = Design Model z (mm). Closure seated at the placement height.
        closure = np.asarray(shown["closure"].vertices)
        assert np.hypot(closure[:, 0], closure[:, 2]).max() == pytest.approx(45.0, abs=1e-3)
        closure_y = closure[:, 1]
        assert closure_y.min() == pytest.approx(SEAT_MM, abs=1e-6)
        assert closure_y.max() == pytest.approx(SEAT_MM + 15.0, abs=1e-6)
        skirt = np.asarray(shown["closure-label-0"].points)
        assert SEAT_MM < skirt[:, 1].min() and skirt[:, 1].max() < SEAT_MM + 15.0
        radius = np.hypot(skirt[:, 0], skirt[:, 2])
        assert radius == pytest.approx(45.2, abs=1e-6)  # on the skirt, 0.2 mm lifted
        body_label = shown["body-label-0"]
        colors = {tuple(color) for color in body_label.colors}
        assert (221, 34, 34) in colors and (34, 34, 221) in colors  # the artwork's own pixels

        # Editing a part's label updates the assembled view.
        labels.show_part("body")
        _add_wrap(labels, "body-band", v_min=0.05, v_max=0.2)
        labels.import_button.click()
        cached = labels._assembled_cache
        labels.show_part("assembled")
        assert labels._assembled_cache is not cached  # label document changed: recomputed
        ids = {object_id for object_id, _kind, _geometry in labels.assembled_geometry}
        assert "body-label-1" in ids
        assert "4 label(s)" in labels.status.text()
        cached = labels._assembled_cache
        labels.show_part("closure")
        labels.show_part("assembled")
        assert labels._assembled_cache is cached  # nothing changed: no OCC work again
    finally:
        window.close()
        app.processEvents()


def test_part_without_design_model_says_what_to_do(app, tmp_path) -> None:
    window = _window(tmp_path)
    try:
        window.new_project(tmp_path / "jar", "Jar")
        labels = window.route_stack.views[Route.LABELS]
        labels.show_part("closure")
        assert labels.workbench.session is None
        assert "No Design Model for Closure yet" in labels.status.text()
        assert not labels.add_zone_button.isEnabled()
        with pytest.raises(Exception, match="part label document is invalid"):
            window.project_manager.record_part_labels(
                "closure",
                {
                    "part": "closure",
                    "design_model_revision_id": "x",
                    "labels": [{"artwork": {"path": "../outside.png"}}],
                },
            )
    finally:
        window.close()
        app.processEvents()


def test_label_strings_have_turkish_entries() -> None:
    texts = set()
    for module in (labels_view,):
        source = Path(module.__file__).read_text(encoding="utf-8")
        texts |= {
            node.args[0].value
            for node in ast.walk(ast.parse(source))
            if isinstance(node, ast.Call)
            and getattr(node.func, "id", None) == "tr"
            and node.args
            and isinstance(node.args[0], ast.Constant)
        }
    texts |= {text for _key, text in labels_view.PART_CHOICES}
    texts |= {text for kinds in labels_view.PART_KINDS.values() for _value, text in kinds}
    texts |= {" and the {part} Design Model", "Re-apply labels to the new Design Model"}
    assert texts - set(i18n.TURKISH) == set()
    assert json.dumps(sorted(texts))  # plain strings only
