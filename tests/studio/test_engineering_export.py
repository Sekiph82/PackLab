from __future__ import annotations

import json

import pytest
from tests.core.test_cad_brep import _inputs
from tests.studio.test_project_scan_master_export import _revision

from packlab_core.cad_brep import revolve_design_model_to_brep
from packlab_core.cad_preview import tessellate_brep_preview
from packlab_core.reconstruction import ScaleState
from packlab_studio.app import create_application
from packlab_studio.engineering_export import (
    DesignModelExportSource,
    EngineeringExportView,
    ExportSourceKind,
)
from packlab_studio.navigation import Route
from packlab_studio.project import ProjectManager


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    application = create_application(["packlab-engineering-export-test"])
    yield application
    application.processEvents()


def _design_source(scale_state: ScaleState = ScaleState.METRIC_UNVERIFIED):
    model, profile, operation = _inputs(scale_state)
    representation = revolve_design_model_to_brep(model, profile, operation)
    preview = tessellate_brep_preview(model, representation)
    return DesignModelExportSource(model, representation, preview, "Bottle Body")


def test_scan_mesh_summary_and_export_delegate_to_selected_scan_master(tmp_path, app) -> None:
    project_manager = ProjectManager()
    project_root = tmp_path / "project"
    project = project_manager.new_project(project_root, "Export UI")
    revision = _revision(project.project_id)
    project_manager.persist_scan_master_revision(revision, expected_revision=0)
    destination = project_root / "export"
    before_metadata = project_manager.current
    before_revision, before_state = project_manager._read_authority(project_manager.layout)
    view = EngineeringExportView(
        project_manager,
        destination_provider=lambda _kind, _initial: destination,
    )

    assert view.selected_source_kind is ExportSourceKind.SCAN_MESH
    assert "Scan Master (captured Scan Mesh)" in view.source_summary.text()
    assert revision.revision_id in view.source_summary.text()
    assert "reconstruction_units" not in view.source_summary.text()
    assert view.available_formats.text() == "PLY, OBJ, GLB"
    assert view.disclaimer.text().find("physical accuracy") >= 0
    view.export_button.click()

    assert "Export complete" in view.status.text()
    output_dirs = tuple((project_root / "export").glob("scan-master-*"))
    assert len(output_dirs) == 1
    manifest = json.loads((output_dirs[0] / "manifest.json").read_text(encoding="ascii"))
    assert manifest["authority_class"] == "SCAN_MASTER"
    assert manifest["scan_master_revision_id"] == revision.revision_id
    after_revision, after_state = project_manager._read_authority(project_manager.layout)
    assert project_manager.current == before_metadata
    assert after_revision == before_revision
    assert after_state == before_state
    selected_revision = project_manager.selected_scan_master_revision()
    assert selected_revision is not None
    assert selected_revision.revision_id == revision.revision_id
    assert selected_revision.mesh == revision.mesh
    assert selected_revision.manifest == revision.manifest
    view.close()
    project_manager.close()


def test_design_model_selection_displays_exact_revision_and_uses_cad_export(tmp_path, app) -> None:
    source = _design_source()
    view = EngineeringExportView(
        design_model_source_provider=lambda: source,
        destination_provider=lambda _kind, _initial: tmp_path,
    )
    view.source_selector.setCurrentIndex(1)
    model_before = source.model.as_dict()
    geometry_digest = source.representation.geometry_sha256
    preview_id = source.preview.revision_id

    assert view.selected_source_kind is ExportSourceKind.DESIGN_MODEL
    assert "editable Design Model" in view.source_summary.text()
    assert source.model.revision_id in view.source_summary.text()
    assert "mm_unverified" in view.source_summary.text()
    assert view.available_formats.text() == "STEP, STL, OBJ + GLB"
    assert "DEFERRED_OWNER_VALIDATION" in view.source_summary.text()
    view.format_selector.setCurrentIndex(view.format_selector.findData("step"))
    view.export_button.click()

    assert "Export complete" in view.status.text()
    output = tmp_path / "Bottle_Body.step"
    metadata = json.loads((tmp_path / "Bottle_Body.step.json").read_text(encoding="ascii"))
    assert output.is_file()
    assert metadata["source_design_model_revision_id"] == source.model.revision_id
    assert source.model.as_dict() == model_before
    assert source.representation.geometry_sha256 == geometry_digest
    assert source.preview.revision_id == preview_id
    view.close()


def test_relative_design_model_gates_step_and_stl_formats(tmp_path, app) -> None:
    source = _design_source(ScaleState.RELATIVE)
    view = EngineeringExportView(
        design_model_source_provider=lambda: source,
        destination_provider=lambda _kind, _initial: tmp_path,
    )
    view.source_selector.setCurrentIndex(1)

    assert view.source_summary.text().find("reconstruction_units") >= 0
    assert view.available_formats.text() == "OBJ + GLB"
    assert view.format_selector.findData("step") == -1
    assert view.format_selector.findData("stl") == -1
    assert view.export_button.isEnabled()
    view.close()


def test_cancel_and_export_error_paths_do_not_mutate_design_authority(
    tmp_path, app, monkeypatch
) -> None:
    source = _design_source()
    view = EngineeringExportView(
        design_model_source_provider=lambda: source,
        destination_provider=lambda _kind, _initial: None,
    )
    view.source_selector.setCurrentIndex(1)
    model_before = source.model.as_dict()
    representation_before = source.representation.as_dict()
    preview_before = source.preview.as_dict()
    view.export_button.click()
    assert view.status.text() == "Export cancelled; no domain service was called."
    assert source.model.as_dict() == model_before
    assert source.representation.as_dict() == representation_before
    assert source.preview.as_dict() == preview_before

    view.destination_provider = lambda _kind, _initial: tmp_path

    def fail_export(*_args, **_kwargs):
        raise ValueError("fixture export failure")

    monkeypatch.setattr("packlab_studio.engineering_export.export_design_model_step", fail_export)
    view.format_selector.setCurrentIndex(view.format_selector.findData("step"))
    view.export_selected()
    assert view.status.text() == "Export failed: fixture export failure"
    assert source.model.as_dict() == model_before
    assert source.representation.as_dict() == representation_before
    assert source.preview.as_dict() == preview_before
    view.close()


def test_export_route_is_project_gated_and_shows_both_source_types(app) -> None:
    from packlab_studio.navigation import RouteStack

    stack = RouteStack()
    view = stack.views[Route.EXPORTS]
    stack.set_project_available(False)
    assert isinstance(view, EngineeringExportView)
    assert view.source_selector.count() == 2
    assert view.source_selector.itemData(0) == ExportSourceKind.SCAN_MESH.value
    assert view.source_selector.itemData(1) == ExportSourceKind.DESIGN_MODEL.value
    assert not view.isEnabled()
    view.source_selector.setCurrentIndex(1)
    assert "No active Design Model source is connected" in view.source_summary.text()
    assert not view.export_button.isEnabled()
    stack.set_project_available(True)
    assert view.isEnabled()
    stack.set_project_available(False)
    assert not view.isEnabled()
    stack.close()
