"""Drive the real StudioMainWindow offscreen through labels, factory export and library.

Run from the repo checkout:
  QT_QPA_PLATFORM=offscreen QT_QPA_FONTDIR=C:\\Windows\\Fonts uv run python <this file>
Fixture: user-authored nominal jar (50 mm tall, 85 mm diameter), synthetic SVG artwork.
"""

import json
import re
import shutil
import struct
import sys
import tempfile
import time
import zipfile
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtPdf import QPdfDocument
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QListWidget, QPushButton

from packlab_studio.app import create_application
from packlab_studio.design_workbench import nominal_jar_design_document
from packlab_studio.engineering_export import ExportSourceKind
from packlab_studio.library_actions import LibraryActionsBar
from packlab_studio.navigation import Route
from packlab_studio.packaging_library_browser import CreatePackagingSkuDialog
from packlab_studio.shell import StudioMainWindow

OUT = Path(r"<USERPROFILE>\Documents\PackLab-work\studio-e2e-labels")
if OUT.exists():
    shutil.rmtree(OUT)
OUT.mkdir(parents=True)
WORK = Path(tempfile.mkdtemp(prefix="packlab-e2e-labels-"))
FILES = OUT / "files"
FILES.mkdir()
checks: dict[str, object] = {"work_dir": str(WORK)}

jar = FILES / "taft-jar-fixture.packlab-design.json"
jar.write_bytes(nominal_jar_design_document(height_mm=50.0, diameter_mm=85.0))
artwork = FILES / "synthetic-label.svg"
artwork.write_text(
    '<svg xmlns="http://www.w3.org/2000/svg" width="240" height="60" viewBox="0 0 240 60">'
    '<rect width="240" height="60" fill="#f3e9d2"/>'
    '<rect x="4" y="4" width="232" height="52" fill="none" stroke="#1b5e20" stroke-width="3"/>'
    '<circle cx="32" cy="30" r="18" fill="#c62828"/>'
    '<path d="M64 18 h150 v8 h-150z M64 34 h110 v8 h-110z" fill="#1b5e20"/></svg>',
    encoding="utf-8",
)

app = create_application(["studio-e2e-labels"])
window = StudioMainWindow(
    packaging_library_root=WORK / "library", diagnostics_root=WORK / "diagnostics"
)
window.resize(1500, 950)
window.show()


def pump(seconds: float = 0.3) -> None:
    end = time.time() + seconds
    while time.time() < end:
        app.processEvents()
        time.sleep(0.02)


def shot(name: str, widget=None) -> None:
    pump(0.3)
    (widget or window).grab().save(str(OUT / f"{name}.png"))
    print("screenshot", name)


def route(label: str) -> None:
    nav = window.findChild(QListWidget, "packlab.navigation.routes")
    for row in range(nav.count()):
        if nav.item(row).text().lower() == label.lower():
            rect = nav.visualItemRect(nav.item(row))
            QTest.mouseClick(nav.viewport(), Qt.MouseButton.LeftButton, pos=rect.center())
            pump()
            return
    raise SystemExit(f"route {label} missing")


def click(parent, name: str) -> None:
    button = parent.findChild(QPushButton, name)
    assert button is not None and button.isEnabled(), name
    QTest.mouseClick(button, Qt.MouseButton.LeftButton)
    pump()


# 1. Labels tab: open the Design Model, wrap label, artwork, dieline, material, mockup.
route("Labels")
labels = window.route_stack.views[Route.LABELS]
labels.choose_design_model_path = lambda: str(jar)
labels.choose_artwork_path = lambda: str(artwork)
labels.choose_directory = lambda _title: str(FILES)
shot("01-labels-empty")
click(labels, "packlab.labels.open-design-model")
print("model:", labels.model_summary.text())
click(labels, "packlab.labels.suggest")
print("suggest:", labels.status.text())
click(labels, "packlab.labels.add-zone")
print("add zone:", labels.status.text())
shot("02-labels-wrap-zone")
click(labels, "packlab.labels.import-artwork")
print("artwork:", labels.status.text())
click(labels, "packlab.labels.export-dieline")
print("dieline:", labels.status.text())
labels.kind.setCurrentIndex(labels.kind.findData("front"))
click(labels, "packlab.labels.add-zone")
checks["front_zone_on_round_jar"] = labels.status.text()
labels.kind.setCurrentIndex(labels.kind.findData("wrap"))
labels.material.setCurrentIndex(labels.material.findData("material-hdpe-white-visual"))
shot("03-labels-artwork-dieline")
started = time.time()
click(labels, "packlab.labels.render")
print("render:", labels.status.text())
while labels._render_thread is not None and labels._render_thread.is_alive():
    pump(1.0)
pump(1.0)
checks["render_seconds"] = round(time.time() - started)
checks["render_status"] = labels.status.text()
print("render done:", labels.status.text())
shot("04-labels-mockup")

dieline = FILES / "taft-jar-fixture-wrap-dieline.svg"
text = dieline.read_text("utf-8")
checks["dieline"] = {
    "width": re.search(r'width="([^"]+)"', text).group(1),
    "height": re.search(r'height="([^"]+)"', text).group(1),
    "scale_mark_10mm": "known-10mm-scale-mark" in text,
    "unit": re.search(r'data-coordinate-unit="([^"]+)"', text).group(1),
}

# 2. Exports page with the Design Model source (needs a project).
window.choose_new_project_path = lambda: str(WORK / "project")
window.new_project_action.trigger()  # File > New Project… (PR #12 menu)
pump()
assert window.project_manager.current is not None, "File > New Project failed"
route("Exports")
exports = window.route_stack.views[Route.EXPORTS]
exports.source_selector.setCurrentIndex(
    exports.source_selector.findData(ExportSourceKind.DESIGN_MODEL.value)
)
export_dir = window.project_manager.layout.path("export")
exports.destination_provider = lambda _kind, _initial: export_dir
shot("05-exports-design-model")
for value in ("step", "stl", "obj_glb", "drawing"):
    exports.format_selector.setCurrentIndex(exports.format_selector.findData(value))
    QTest.mouseClick(exports.export_button, Qt.MouseButton.LeftButton)
    pump()
    print(value, "->", exports.status.text()[:160])
shot("06-exports-done")

step = (export_dir / "taft-jar-fixture.step").read_text("utf-8", errors="replace")
stl = (export_dir / "taft-jar-fixture.stl").read_bytes()
triangles = (
    struct.unpack("<I", stl[80:84])[0]
    if not stl.startswith(b"solid")
    else stl.count(b"facet normal")
)
pdf = QPdfDocument()
pdf.load(str(export_dir / "taft-jar-fixture-dimension-sheet.pdf"))
checks["step_header"] = step.splitlines()[:4]
checks["step_units"] = sorted(set(re.findall(r"SI_UNIT\(([^)]*)\)", step)))[:4]
checks["stl"] = {"bytes": len(stl), "triangles": triangles}
checks["pdf_pages"] = pdf.pageCount()
checks["export_files"] = sorted(path.name for path in export_dir.iterdir())
for path in export_dir.iterdir():
    shutil.copy2(path, FILES / path.name)

# 3. Library: create asset, SKU, backup, restore, contact sheet.
route("Library")
library = window.route_stack.views[Route.LIBRARY]
bar = library.findChild(LibraryActionsBar)
click(bar, "packlab.library.new-asset.create")
print("asset:", bar.status.text())
shot("07-library-asset")


def fill_sku() -> None:
    dialog = next(
        w
        for w in QApplication.topLevelWidgets()
        if isinstance(w, CreatePackagingSkuDialog) and w.isVisible()
    )
    dialog.resize(700, 650)
    dialog.sku_id_field.setText("TAFT-JAR-E2E")
    dialog.display_name_field.setText("Taft jar (fixture) wrap label")
    item = dialog.artwork_view.item(0)
    item.setCheckState(Qt.CheckState.Checked)
    pump(0.3)
    dialog.grab().save(str(OUT / "08-create-sku-dialog.png"))
    save = dialog.findChild(QPushButton, "packlab.library.create-sku.save")
    QTest.mouseClick(save, Qt.MouseButton.LeftButton)


QTimer.singleShot(300, fill_sku)
QTest.mouseClick(library.create_sku_button, Qt.MouseButton.LeftButton)
pump()
snapshot = window.packaging_library_service.audit_store.snapshot()
checks["skus"] = [
    {"sku_id": s.sku_id, "artwork_variants": [a.variant_id for a in s.artwork_references]}
    for s in snapshot.skus
]
checks["audit_events"] = [e.operation_type for e in snapshot.events]
shot("09-library-sku")
archive = WORK / "library-backup.zip"
bar.choose_backup_path = lambda: str(archive)
click(bar, "packlab.library.backup")
print("backup:", bar.status.text())
restored = WORK / "restored-library"
bar.choose_archive_path = lambda: str(archive)
bar.choose_directory = lambda _title: str(restored)
click(bar, "packlab.library.restore")
print("restore:", bar.status.text())
shot("10-library-restored")
sheets = WORK / "contact-sheets"
sheets.mkdir()
bar.choose_directory = lambda _title: str(sheets)
click(bar, "packlab.library.contact-sheet")
print("contact sheet:", bar.status.text())
shot("11-library-contact-sheet")
sheet = next(sheets.glob("*/contact-sheet.png"))
shutil.copy2(sheet, FILES / "contact-sheet.png")
shutil.copy2(archive, FILES / "library-backup.zip")
checks["backup_entries"] = len(zipfile.ZipFile(archive).namelist())
checks["restored_state"] = (restored / "packaging-library-state.json").is_file()
# 4. Real scan-fitted Design Model from the Measure & Design e2e project (test-333 jar):
#    File > Open Project on a copy; Labels picks the saved revision up automatically.
REAL = Path(r"<USERPROFILE>\Documents\PackLab-work\studio-e2e-measure\project")
real_copy = WORK / "measure-project-copy"
shutil.copytree(REAL, real_copy)
window.choose_open_project_path = lambda: str(real_copy)
window.open_project_action.trigger()
pump()
route("Labels")
print("real model:", labels.model_summary.text())
checks["real_model_summary"] = labels.model_summary.text()
labels.kind.setCurrentIndex(labels.kind.findData("wrap"))
click(labels, "packlab.labels.suggest")
click(labels, "packlab.labels.add-zone")
checks["real_wrap"] = labels.status.text()
print("real wrap:", labels.status.text())
click(labels, "packlab.labels.import-artwork")
real_files = FILES / "real-test-333"
real_files.mkdir()
labels.choose_directory = lambda _title: str(real_files)
click(labels, "packlab.labels.export-dieline")
checks["real_dieline"] = labels.status.text()
shot("12-real-scan-wrap-label")
click(labels, "packlab.labels.render")
while labels._render_thread is not None and labels._render_thread.is_alive():
    pump(1.0)
pump(1.0)
checks["real_render_status"] = labels.status.text()
shot("13-real-scan-mockup")
real_json = next(real_files.glob("*-dieline.json"))
checks["real_label_host"] = json.loads(real_json.read_text("utf-8"))["label_host"]

mockups = sorted(FILES.glob("**/*-mockup*/renders/standard_views/*.png"))
checks["mockup_pngs"] = [str(p) for p in mockups]
(OUT / "checks.json").write_text(json.dumps(checks, indent=2), encoding="utf-8")
print(json.dumps(checks, indent=2))
window.close()
pump()
sys.exit(0)
