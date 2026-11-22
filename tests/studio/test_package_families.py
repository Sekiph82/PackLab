"""Package families route (PL-0459) driven through the real StudioMainWindow offscreen.

Fixtures are synthetic: nominal presets typed into the window (standalone roots) and the
synthetic jar + A4 mat scene from test_measure_design (captured lineage). Passing proves the
wiring, authority and export path, not physical accuracy.
"""

from __future__ import annotations

import json

import pytest

pytest.importorskip("cv2")
pytest.importorskip("open3d")

from PySide6.QtCore import QSettings  # noqa: E402
from tests.studio.test_measure_design import _promoted_design  # noqa: E402

from packlab_core.design_model import FeatureKind  # noqa: E402
from packlab_studio import package_families as pf  # noqa: E402
from packlab_studio.app import create_application  # noqa: E402
from packlab_studio.engineering_export import (  # noqa: E402
    EngineeringExportView,
    ExportSourceKind,
)
from packlab_studio.navigation import Route  # noqa: E402
from packlab_studio.package_families_view import PackageFamiliesView  # noqa: E402
from packlab_studio.project import ProjectError  # noqa: E402
from packlab_studio.viewport import SceneObjectKind  # noqa: E402


@pytest.fixture
def window(monkeypatch, tmp_path):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    create_application(["packlab-package-families"])
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    QSettings.setPath(
        QSettings.Format.IniFormat, QSettings.Scope.UserScope, str(tmp_path / "settings")
    )
    from packlab_studio.shell import StudioMainWindow

    studio = StudioMainWindow(
        diagnostics_root=tmp_path / "diagnostics", packaging_library_root=tmp_path / "library"
    )
    yield studio
    studio.close()


def _families(window) -> PackageFamiliesView:
    view = window.route_stack.views[Route.PACKAGE_FAMILIES]
    assert isinstance(view, PackageFamiliesView)
    return view


def _choose(view: PackageFamiliesView, family: str, preset: str, source: str) -> None:
    view.family.setCurrentIndex(view.family.findData(family))
    view.preset.setCurrentText(preset)
    view.source.setCurrentIndex(view.source.findData(source))


def _export(window, tmp_path, part: str, fmt: str):
    view = _families(window)
    view.part.setCurrentIndex(view.part.findData(part))
    view.export_button.click()
    exports = window.route_stack.views[Route.EXPORTS]
    assert isinstance(exports, EngineeringExportView)
    assert window.navigation.current_route is Route.EXPORTS
    assert exports.selected_source_kind is ExportSourceKind.DESIGN_MODEL
    target = window.project_manager.layout.path("export") / "families"
    target.mkdir(parents=True, exist_ok=True)
    exports.destination_provider = lambda _kind, _initial: target
    exports.format_selector.setCurrentIndex(exports.format_selector.findData(fmt))
    exports.export_selected()
    assert exports.status.text().startswith("Export complete"), exports.status.text()
    return sorted(target.glob(f"*{part}*.{fmt}"))


@pytest.mark.parametrize(
    ("family", "preset", "edited", "part"),
    [
        ("jerrycan", "5 L jerrycan", ("width", 200.0), "body"),
        ("trigger_pump", "500 ml trigger sprayer bottle", ("body_height", 175.0), "bottle"),
        ("tube", "100 ml cosmetic tube", ("body_length", 120.0), "tube"),
    ],
)
def test_standalone_family_create_edit_save_reopen_export(
    window, tmp_path, family, preset, edited, part
) -> None:
    window.new_project(tmp_path / "project", "Families")
    view = _families(window)
    _choose(view, family, preset, "standalone")
    view.create_button.click()
    design = view.design
    assert design is not None, view.status.text()
    assert design.model.parent_kind.value == "STANDALONE_DESIGN_GEOMETRY"
    root = design.model.standalone_root
    assert root is not None and root.source_kind.value == "USER_AUTHORED_NOMINAL_DIMENSIONS"
    assert root.project_id == window.project_manager.current.project_id
    assert design.model.physical_accuracy_validation_status == "DEFERRED_OWNER_VALIDATION"
    assert design.model.mold_use_authorized is False
    assert {item.name for item in design.parts} >= {part}
    assert view.viewer.service.scene.visible_objects()

    name, value = edited
    view.spins[name].setValue(value)
    view.apply_button.click()
    edited_design = view.design
    assert edited_design.model.previous_revision_id == design.model.revision_id
    assert edited_design.parameters[name] == value
    if family == "jerrycan":
        assert edited_design.overall_dimensions()["width"] == pytest.approx(200.0, abs=0.01)

    view.save_button.click()
    assert "current Design Model" in view.status.text(), view.status.text()
    record, document = window.project_manager.selected_design_model()
    assert record["revision_id"] == edited_design.model.revision_id
    assert record["parent_kind"] == "STANDALONE_DESIGN_GEOMETRY"
    assert record["scan_master_revision_id"] is None
    assert record["standalone_root_revision_id"] == root.revision_id
    assert document["package_family_workflow"]["family"] == family
    labels = window.route_stack.views[Route.LABELS]
    labels.use_project_model()
    assert "Labels currently support Measure & Design jar/bottle revisions" in (
        labels.status.text()
    ), labels.status.text()
    assert pf.FAMILIES[family] in labels.status.text()

    view.design = None
    view.open_button.click()
    assert view.design is not None and view.design.model == edited_design.model, view.status.text()

    steps = _export(window, tmp_path, part, "step")
    assert steps and steps[0].read_bytes().startswith(b"ISO-10303-21")
    stls = _export(window, tmp_path, part, "stl")
    assert stls and stls[0].stat().st_size > 1000


def test_jerrycan_handle_opening_is_cut_through_the_body(window, tmp_path) -> None:
    from OCP.BRepClass3d import BRepClass3d_SolidClassifier
    from OCP.gp import gp_Pnt
    from OCP.TopAbs import TopAbs_IN, TopAbs_OUT

    from packlab_core.cad_adapter import _shape_for_handle

    window.new_project(tmp_path / "project", "Jerrycan")
    view = _families(window)
    _choose(view, "jerrycan", "5 L jerrycan", "standalone")
    view.create_button.click()
    design = view.design
    assert design is not None, view.status.text()
    p = design.parameters
    shape = _shape_for_handle(design.part("body").representation.shape_handle)
    top = p["body_height"] + p["shoulder_height"] + p["handle_height"]
    x = p["width"] / 2 - 0.08 * p["width"] - p["handle_opening_width"] / 2
    z = top - p["handle_grip_thickness"] - p["handle_opening_height"] / 2
    for y in (-15.0, 0.0, 15.0):  # through the full bridge depth, both sides of y = 0
        assert BRepClass3d_SolidClassifier(shape, gp_Pnt(x, y, z), 1e-6).State() == TopAbs_OUT
    grip = BRepClass3d_SolidClassifier(shape, gp_Pnt(x, 0.0, top - 4.0), 1e-6)
    assert grip.State() == TopAbs_IN
    assert any(item.feature_kind is FeatureKind.HANDLE_OPENING for item in design.model.features)
    assert design.overall_dimensions()["depth"] == pytest.approx(p["depth"], abs=0.5)


def test_pouch_artwork_and_no_brep_export(window, tmp_path) -> None:
    window.new_project(tmp_path / "project", "Pouch")
    view = _families(window)
    _choose(view, "pouch", "Sachet 80 x 120 mm", "standalone")
    assert view.source.findData("captured") == -1  # core pouch is model-only
    view.create_button.click()
    design = view.design
    assert design is not None and not design.parts, view.status.text()
    assert not view.export_button.isEnabled()
    assert view.export_source() is None
    artwork = tmp_path / "art.svg"
    artwork.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="80" height="120" viewBox="0 0 80 120">'
        '<rect width="80" height="120" fill="#cde"/></svg>',
        encoding="utf-8",
    )
    view._choose_artwork = lambda _parent: str(artwork)
    view.artwork_button.click()
    assert view.design.extra["artwork"]["asset"]["media_type"] == "image/svg+xml", (
        view.status.text()
    )
    view.save_button.click()
    record, document = window.project_manager.selected_design_model()
    assert record["parent_kind"] == "STANDALONE_DESIGN_GEOMETRY"
    workflow = document["package_family_workflow"]
    assert workflow["artwork"]["surface_feature_id"] == workflow["pouch_family"]["front_feature_id"]
    assert document["overall_dimensions_mm_unverified"]["width"] == pytest.approx(80.0)


def test_closure_on_captured_jar_assembly_visibility_and_replacement(window, tmp_path) -> None:
    measure = _promoted_design(window, tmp_path)
    measure.save_button.click()
    jar_record, _ = window.project_manager.selected_design_model()
    scan_master_id = measure.scan_master.revision_id

    view = _families(window)
    _choose(view, "closure", "Screw cap sized from the container", "captured")
    assert view.source.findData("standalone") == -1
    assert view.spins["closure_line"].value() > 0, view.status.text()
    view.create_button.click()
    design = view.design
    assert design is not None, view.status.text()
    assert design.model.previous_revision_id == jar_record["revision_id"]
    assert design.model.fitted_to_scan_master_revision_id == scan_master_id
    assert {item.name for item in design.parts} == {"container", "cap"}
    cap_feature, _parameter, values = pf.current_cap(design)
    assert values["thread_compatibility_claimed"] is False
    assert values["internal_thread_geometry_modelled"] is False
    line = view.spins["closure_line"].value()
    container = design.part("container").preview.preview_bounds
    cap = design.part("cap").preview.preview_bounds
    assert container[5] == pytest.approx(line, abs=0.05)  # container clipped at the line
    assert cap[4] == pytest.approx(line, abs=0.05)
    assert design.extra["assembly"]["container_source_revision_id"] == jar_record["revision_id"]

    # Visibility goes through ClosureWorkflowController (CAP scene objects only).
    scene = view.viewer.service.scene
    assert scene.get("cap").kind is SceneObjectKind.CAP
    view.show_closure.setChecked(False)
    assert not view.viewer.service.scene.get("cap").visible
    view.show_closure.setChecked(True)

    view.save_button.click()
    record, document = window.project_manager.selected_design_model()
    assert record["parent_kind"] == "CAPTURED_SCAN_MASTER"
    assert record["scan_master_revision_id"] == scan_master_id
    assert document["package_family_workflow"]["assembly"]["thread_compatibility_claimed"] is False

    # The synthetic scene's Scan Master is a noisy object mesh (the real test-333 scan is
    # refused with section_insufficient_points): core must refuse it and nothing changes. Dense
    # scan is covered by test_closure_replacement_undo_redo_through_the_controller.
    before = view.design.model.revision_id
    view.spins["cap_diameter"].setValue(view.spins["cap_diameter"].value() + 2.0)
    view.replace_button.click()
    assert "core mating references refused: neck_section_quality_invalid" in (view.status.text()), (
        view.status.text()
    )
    assert view.design.model.revision_id == before
    assert pf.current_cap(view.design)[0] == cap_feature
    assert not view.undo_button.isEnabled()

    steps = _export(window, tmp_path, "cap", "step")
    assert steps and steps[0].read_bytes().startswith(b"ISO-10303-21")


def test_tube_bound_to_scan_master_and_closure_needs_a_container(window, tmp_path) -> None:
    measure = _promoted_design(window, tmp_path)
    view = _families(window)
    _choose(view, "closure", "Screw cap sized from the container", "captured")
    view.create_button.click()  # no Design Model saved yet
    assert view.design is None and "Measure & Design" in view.status.text()

    _choose(view, "tube", "50 ml tube", "captured")
    view.create_button.click()
    design = view.design
    assert design is not None, view.status.text()
    assert design.model.parent_kind.value == "CAPTURED_SCAN_MASTER"
    assert design.model.fitted_to_scan_master_revision_id == measure.scan_master.revision_id
    view.save_button.click()
    assert window.project_manager.selected_design_model()[0]["parent_kind"] == (
        "CAPTURED_SCAN_MASTER"
    )

    _choose(view, "jerrycan", "5 L jerrycan", "captured")
    view.create_button.click()  # a round jar is not a jerrycan section loft
    assert "failed" in view.status.text()


def test_standalone_persist_refuses_foreign_or_tampered_documents(window, tmp_path) -> None:
    window.new_project(tmp_path / "project", "Authority")
    manager = window.project_manager
    design = pf.create_standalone(
        "tube",
        pf.default_parameters("tube"),
        project_id="00000000-0000-4000-8000-000000000000",
        preset="",
        actor_id="owner",
    )
    with pytest.raises(ProjectError, match="invalid|does not match"):
        manager.persist_design_model_revision(
            design.as_dict(), expected_revision=manager.current.revision
        )
    own = pf.create_standalone(
        "tube",
        pf.default_parameters("tube"),
        project_id=manager.current.project_id,
        preset="",
        actor_id="owner",
    )
    tampered = own.as_dict()
    body = json.loads(tampered["design_document"])
    body["body"]["model"]["reason"] = "tampered"
    tampered["design_document"] = json.dumps(body)
    with pytest.raises(ProjectError, match="standalone design document"):
        manager.persist_design_model_revision(tampered, expected_revision=manager.current.revision)
    record = manager.persist_design_model_revision(
        own.as_dict(), expected_revision=manager.current.revision
    )
    assert record["parent_kind"] == "STANDALONE_DESIGN_GEOMETRY"
    assert pf.load_family_document(manager.selected_design_model()[1]).model == own.model


def _dense_jar_scan_master(project_id: str):
    """Synthetic round jar: body r=35 to z=34, lid r=33.5 to z=40, rings every 0.5 mm."""
    import hashlib
    import math

    from packlab_core.geometry_adapter import TriangleMeshData
    from packlab_core.scan_master import ScanMasterRevision, mesh_sha256

    count = 96
    levels = [index * 0.5 for index in range(81)]
    vertices = [
        (
            (35.0 if z <= 34.0 else 33.5) * math.cos(math.tau * i / count),
            (35.0 if z <= 34.0 else 33.5) * math.sin(math.tau * i / count),
            z,
        )
        for z in levels
        for i in range(count)
    ]
    faces = []
    for level in range(len(levels) - 1):
        for i in range(count):
            a, b = level * count + i, level * count + (i + 1) % count
            c, d = b + count, a + count
            faces.extend(((a, b, c), (a, c, d)))
    mesh = TriangleMeshData(tuple(vertices), tuple(faces))
    revision_id = f"scan-master:{hashlib.sha256(b'dense-jar').hexdigest()}"
    return ScanMasterRevision(
        revision_id,
        project_id,
        mesh,
        {
            "scan_master_revision_id": revision_id,
            "project_id": project_id,
            "authority_class": "SCAN_MASTER",
            "raw_capture_revision_id": "capture-r1",
            "raw_capture_sha256": "b" * 64,
            "reconstruction_revision_id": "reconstruction-r1",
            "parent_object_geometry_revision_id": "object-r1",
            "scale_provenance_id": "scale-r1",
            "scale_state": "metric-unverified",
            "output_geometry_sha256": mesh_sha256(mesh),
            "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
            "mold_use_authorized": False,
            "known_limitations": ["synthetic test revision"],
            "coverage_gaps": [],
            "promotion_actor": "operator-test",
            "promotion_reason": "Dense synthetic jar for closure replacement.",
            "hole_report": {"parent_revision_id": "cleanup-r1"},
        },
    )


def test_closure_replacement_undo_redo_through_the_controller(window, tmp_path) -> None:
    from packlab_studio import measure_design as md

    window.new_project(tmp_path / "project", "Dense jar")
    manager = window.project_manager
    scan = _dense_jar_scan_master(manager.current.project_id)
    manager.persist_scan_master_revision(scan, expected_revision=manager.current.revision)
    jar = md.fit_design_model(scan, actor_id="owner", owner_review=True)
    manager.persist_design_model_revision(jar.as_dict(), expected_revision=manager.current.revision)

    view = _families(window)
    _choose(view, "closure", "63 mm screw cap", "captured")
    view.spins["closure_line"].setValue(34.0)
    view.create_button.click()
    created = view.design
    assert created is not None, view.status.text()
    old_cap, _pid, _values = pf.current_cap(created)

    view.spins["cap_diameter"].setValue(68.0)
    view.replace_button.click()
    assert view.status.text().startswith("Replace closure:"), view.status.text()
    replaced = view.design
    new_cap, _pid, values = pf.current_cap(replaced)
    assert new_cap != old_cap and values["cap_diameter"] == 68.0
    report = replaced.extra["closure_replacement"]
    assert report["previous_model_revision_id"] == created.model.revision_id
    assert report["scan_master_mutated"] is False
    assert report["thread_compatibility_claimed"] is False
    assert replaced.part("cap").preview.preview_bounds[1] == pytest.approx(34.0, abs=0.05)
    assert view.undo_button.isEnabled() and not view.redo_button.isEnabled()

    view.undo_button.click()
    assert pf.current_cap(view.design)[0] == old_cap, view.status.text()
    assert view.redo_button.isEnabled()
    view.redo_button.click()
    assert pf.current_cap(view.design)[0] == new_cap, view.status.text()

    view.save_button.click()
    record, document = manager.selected_design_model()
    assert record["revision_id"] == view.design.model.revision_id
    assert pf.load_family_document(document).model == view.design.model


def test_reload_refuses_a_different_loft_mode_or_brep(window, tmp_path) -> None:
    from packlab_core.cad_brep import loft_design_model_to_brep
    from packlab_core.design_operations import LoftSectionInput

    window.new_project(tmp_path / "project", "Reload")
    manager = window.project_manager
    design = pf.create_standalone(
        "jerrycan",
        pf.default_parameters("jerrycan"),
        project_id=manager.current.project_id,
        preset="5 L jerrycan",
        actor_id="owner",
    )
    document = design.as_dict()
    parts = {item["name"]: item for item in document["package_family_workflow"]["parts"]}
    assert parts["body"]["build_mode"] == "loft_ruled+parametric_handle_cut"
    assert parts["spout"]["build_mode"] == "revolve"
    body = design.part("body")
    assert parts["body"]["brep_geometry_sha256"] == body.representation.geometry_sha256
    assert pf.load_family_document(document).model == design.model

    # A smooth (non-ruled) loft of the same operation is a different BREP, same operation id.
    smooth = loft_design_model_to_brep(
        design.model,
        tuple(
            LoftSectionInput(feature_id, section, z)
            for feature_id, z, section in zip(
                body.operation.parent_feature_ids,
                body.operation.section_positions,
                _sections(design, body.operation.input_ids),
                strict=True,
            )
        ),
        body.operation,
    )
    assert smooth.revision_id != body.representation.revision_id

    for key, value in (
        ("build_mode", "loft_smooth"),
        ("brep_revision_id", smooth.revision_id),
    ):
        tampered = json.loads(json.dumps(document))
        for item in tampered["package_family_workflow"]["parts"]:
            if item["name"] == "body":
                item[key] = value
        with pytest.raises(pf.PackageFamilyError, match="body.*not opened as the same model"):
            pf.load_family_document(tampered)


def _sections(design, section_ids):
    from packlab_core.design_serialization import deserialize_design_model

    sections = {
        item.section_id: item
        for item in deserialize_design_model(design.design_document).cross_sections
    }
    return tuple(sections[section_id] for section_id in section_ids)


def test_preset_logic_uses_item_data_not_translated_text(window) -> None:
    view = _families(window)
    view.family.setCurrentIndex(view.family.findData("jerrycan"))
    names = list(pf.PRESETS["jerrycan"])
    assert len(names) >= 2
    view.preset.setCurrentIndex(1)
    for index in range(view.preset.count()):  # what a Turkish relabel would do
        view.preset.setItemText(index, f"translated {index}")
    view._preset_changed()
    assert view._preset_key() == names[1]
    expected = pf.default_parameters("jerrycan", names[1])
    assert all(
        view.values()[key] == value for key, value in expected.items() if key in view.values()
    )
