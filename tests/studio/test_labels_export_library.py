"""PL-0448/0449/0460/0461: labels, factory export and library actions in the Studio window."""

from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path

import pytest
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QDialog, QPushButton

from packlab_core.cad_label_surface_analysis import (
    CadLabelSurfacePolicy,
    analyze_cad_label_surfaces,
)
from packlab_core.label_zone import LabelZoneKind
from packlab_core.packaging_sku_library import PackagingSkuStatus
from packlab_studio import design_workbench
from packlab_studio.app import create_application
from packlab_studio.design_workbench import (
    DesignWorkbench,
    DesignWorkbenchError,
    load_design_model_session,
    nominal_jar_design_document,
)
from packlab_studio.engineering_export import EngineeringExportView, ExportSourceKind
from packlab_studio.labels_view import LabelsView
from packlab_studio.library_actions import LibraryActionsBar
from packlab_studio.navigation import Route
from packlab_studio.packaging_library_browser import CreatePackagingSkuDialog
from packlab_studio.shell import StudioMainWindow

SVG = (
    b'<svg xmlns="http://www.w3.org/2000/svg" width="200" height="40" viewBox="0 0 200 40">'
    b'<rect width="200" height="40" fill="#d22"/><circle cx="20" cy="20" r="15" fill="#22d"/>'
    b"</svg>"
)


@pytest.fixture
def app(monkeypatch) -> QApplication:
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    return create_application(["packlab-labels-test"])


@pytest.fixture
def jar_file(tmp_path: Path) -> Path:
    path = tmp_path / "taft-jar.packlab-design.json"
    path.write_bytes(
        nominal_jar_design_document(
            height_mm=50, diameter_mm=85, created_at_utc="2026-11-20T00:00:00Z"
        )
    )
    return path


@pytest.fixture
def window(app, tmp_path: Path):
    shell = StudioMainWindow(
        packaging_library_root=tmp_path / "library", diagnostics_root=tmp_path / "diag"
    )
    yield shell
    shell.close()
    app.processEvents()


def _click(widget, name: str) -> None:
    button = widget.findChild(QPushButton, name)
    assert button is not None, name
    assert button.isEnabled(), name
    button.click()


def test_nominal_jar_round_trips_and_keeps_one_exact_cylinder_band_per_segment(jar_file) -> None:
    session = load_design_model_session(jar_file)
    x0, y0, z0, x1, y1, z1 = session.bounds_mm
    assert (z1 - z0, x1 - x0, y1 - y0) == pytest.approx((50.0, 85.0, 85.0))
    assert session.model.coordinate_unit == "mm_unverified"
    analysis = analyze_cad_label_surfaces(
        session.model, session.representation, CadLabelSurfacePolicy((0.0, 1.0, 0.0), 90.0, 1.0)
    )
    cylinders = {item.center[2] for item in analysis.candidates if "Cylinder" in item.surface_type}
    assert len(cylinders) == 6  # two 25 mm bands x three sampled rows, not 256 slivers


def test_wrap_label_dieline_and_artwork_on_revolved_jar(app, jar_file, tmp_path) -> None:
    workbench = DesignWorkbench()
    workbench.open_document(jar_file)
    entry = workbench.add_label_zone(workbench.suggest_label_zone(LabelZoneKind.WRAP))
    assert entry.metric_binding.mapping_mode == "CYLINDRICAL_WRAP"
    assert entry.metric_binding.host_width_mm_unverified == pytest.approx(85.0 * 3.141592653589793)
    width, height = entry.size_mm
    assert (width, height) == pytest.approx((267.035, 20.0), abs=1e-3)
    workbench.import_artwork(entry, SVG)
    path, export = workbench.export_dieline_svg(entry, tmp_path)
    text = path.read_text("utf-8")
    assert 'data-coordinate-unit="mm_unverified"' in text
    assert "known-10mm-scale-mark" in text
    assert re.search(r'width="([0-9.]+)mm"', text).group(1).startswith("274.03")  # + bleed/margin
    assert export.height_mm_unverified == pytest.approx(34.0)
    assert json.loads(path.with_suffix(".json").read_text("utf-8"))["print_ready"] is False
    references = workbench.sku_artwork_references()
    assert len(references) == 1 and references[0].variant_id == "wrap"
    with pytest.raises(DesignWorkbenchError, match="wrap label"):
        workbench.suggest_label_zone(LabelZoneKind.FRONT)


def test_mockup_without_blender_shows_clear_message(app, jar_file, tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(design_workbench, "find_blender", lambda: None)
    workbench = DesignWorkbench()
    workbench.open_document(jar_file)
    view = LabelsView(workbench)
    view.choose_directory = lambda _title: str(tmp_path)
    _click(view, "packlab.labels.render")
    assert "Blender 5.x was not found" in view.status.text()


def test_mockup_scene_package_is_built_from_the_label_chain(app, jar_file, tmp_path) -> None:
    fake_blender = tmp_path / "blender.exe"
    fake_blender.write_bytes(b"not run")
    workbench = DesignWorkbench()
    workbench.open_document(jar_file)
    entry = workbench.add_label_zone(workbench.suggest_label_zone(LabelZoneKind.WRAP))
    workbench.import_artwork(entry, SVG)
    workbench.set_material("material-pet-clear-visual")
    try:
        job = workbench.prepare_mockup(tmp_path, executable=fake_blender)
    except DesignWorkbenchError as error:  # no git and no build revision: provenance refused
        assert "build revision" in str(error)
        return
    overlays = job.package.manifest()["body"]["scene"]["overlays"]
    assert [item["mapping_mode"] for item in overlays] == ["CYLINDRICAL_WRAP"]
    assert (job.root / "assets" / "label-0.png").read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    assert job.bounds_max[2] == pytest.approx(0.05)


def test_labels_tab_buttons_drive_the_workbench(window, jar_file, tmp_path) -> None:
    labels = window.route_stack.views[Route.LABELS]
    assert isinstance(labels, LabelsView)
    labels.choose_design_model_path = lambda: str(jar_file)
    artwork = tmp_path / "art.svg"
    artwork.write_bytes(SVG)
    labels.choose_artwork_path = lambda: str(artwork)
    out = tmp_path / "out"
    out.mkdir()
    labels.choose_directory = lambda _title: str(out)
    _click(labels, "packlab.labels.open-design-model")
    assert "height 50.0 mm" in labels.model_summary.text()
    _click(labels, "packlab.labels.suggest")
    assert "cylinder region" in labels.status.text()
    _click(labels, "packlab.labels.add-zone")
    assert "Added wrap label: 267.0 x 20.0" in labels.status.text()
    _click(labels, "packlab.labels.import-artwork")
    assert "Placed art.svg" in labels.status.text()
    _click(labels, "packlab.labels.export-dieline")
    assert (out / "taft-jar-wrap-dieline.svg").is_file()
    labels.kind.setCurrentIndex(labels.kind.findData("front"))
    _click(labels, "packlab.labels.add-zone")
    assert labels.status.text().startswith("Not done: No flat front panel")


def test_exports_page_gets_design_model_and_dimension_sheet(window, jar_file, tmp_path) -> None:
    window.design_workbench.open_document(jar_file)
    window.new_project(tmp_path / "project", "Jar")
    exports = window.route_stack.views[Route.EXPORTS]
    assert isinstance(exports, EngineeringExportView)
    exports.source_selector.setCurrentIndex(
        exports.source_selector.findData(ExportSourceKind.DESIGN_MODEL.value)
    )
    destination = window.project_manager.layout.path("export")
    exports.destination_provider = lambda _kind, _initial: destination
    for value in ("step", "stl", "obj_glb", "drawing"):
        exports.format_selector.setCurrentIndex(exports.format_selector.findData(value))
        exports.export_button.click()
        assert exports.status.text().startswith("Export complete"), exports.status.text()
    names = sorted(path.name for path in destination.iterdir())
    for expected in (
        "taft-jar.step",
        "taft-jar.stl",
        "taft-jar.obj",
        "taft-jar.glb",
        "taft-jar-dimension-sheet.pdf",
        "taft-jar-dimension-sheet.svg",
        "taft-jar-dimension-sheet.dxf",
    ):
        assert expected in names
    assert (destination / "taft-jar.step").read_bytes().startswith(b"ISO-10303-21;")
    assert (destination / "taft-jar-dimension-sheet.pdf").read_bytes().startswith(b"%PDF")


def test_library_asset_sku_backup_restore_and_contact_sheet(window, jar_file, tmp_path) -> None:
    workbench = window.design_workbench
    workbench.open_document(jar_file)
    entry = workbench.add_label_zone(workbench.suggest_label_zone(LabelZoneKind.WRAP))
    workbench.import_artwork(entry, SVG)
    library = window.route_stack.views[Route.LIBRARY]
    bar = library.findChild(LibraryActionsBar)
    assert bar is not None
    _click(bar, "packlab.library.new-asset.create")
    assert bar.status.text().startswith("Created"), bar.status.text()
    snapshot = window.packaging_library_service.audit_store.snapshot()
    assert len(snapshot.assets) == 1
    document = json.loads(snapshot.assets[0].canonical_json)
    assert document["source_links"]["design_models"][0]["revision_id"] == (
        workbench.session.model.revision_id
    )
    assert document["dimensions"]["overall_height"] == {"value": 50.0, "unit": "mm"}
    assert library.selected_asset_id == snapshot.assets[0].asset_id

    def fill_dialog() -> None:
        dialog = next(
            widget
            for widget in QApplication.topLevelWidgets()
            if isinstance(widget, CreatePackagingSkuDialog) and widget.isVisible()
        )
        dialog.sku_id_field.setText("TAFT-JAR-250")
        dialog.display_name_field.setText("Taft jar 250 g")
        dialog.status_selector.setCurrentIndex(
            dialog.status_selector.findData(PackagingSkuStatus.DRAFT)
        )
        dialog.artwork_view.item(0).setCheckState(dialog.artwork_view.item(0).checkState().Checked)
        dialog._create()
        if dialog.result() != QDialog.DialogCode.Accepted:
            dialog.reject()

    QTimer.singleShot(0, fill_dialog)
    library.create_sku_button.click()
    skus = window.packaging_library_service.audit_store.snapshot().skus
    assert [item.sku_id for item in skus] == ["TAFT-JAR-250"]
    assert skus[0].artwork_references[0].variant_id == "wrap"

    archive = tmp_path / "backup.zip"
    bar.choose_backup_path = lambda: str(archive)
    _click(bar, "packlab.library.backup")
    assert zipfile.is_zipfile(archive), bar.status.text()
    restored = tmp_path / "restored"
    bar.choose_archive_path = lambda: str(archive)
    bar.choose_directory = lambda _title: str(restored)
    _click(bar, "packlab.library.restore")
    assert bar.status.text().startswith("Restored"), bar.status.text()
    assert (restored / "packaging-library-state.json").is_file()
    sheets = tmp_path / "sheets"
    sheets.mkdir()
    bar.choose_directory = lambda _title: str(sheets)
    _click(bar, "packlab.library.contact-sheet")
    assert bar.status.text().startswith("Contact sheet written"), bar.status.text()
    assert list(sheets.glob("*/contact-sheet.png"))
