"""Drive the real StudioMainWindow offscreen through Package families (PL-0459).

Run from the PackLab checkout:
  QT_QPA_PLATFORM=offscreen QT_QPA_FONTDIR=C:\\Windows\\Fonts uv run python <this file>
1. Copy of the real test-333 jar project: fit + save the jar Design Model, add a screw cap
   (captured lineage), toggle the closure, try a closure replacement, export STEP/STL.
2. New project: 5 L jerrycan, trigger bottle, tube (and a sachet) from presets (standalone
   ADR-0005 roots), save, export STEP/STL. Exported files are re-read and measured.
"""

import json
import re
import shutil
import struct
import sys
import time
from pathlib import Path

from PySide6.QtCore import QSettings, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QListWidget

from packlab_studio.app import create_application
from packlab_studio.engineering_export import ExportSourceKind
from packlab_studio.navigation import Route

WORK = Path(r"<USERPROFILE>\Documents\PackLab-work")
OUT = WORK / "final-walkthrough-families"
REAL = WORK / "studio-e2e-measure" / "project"
if OUT.exists():
    shutil.rmtree(OUT)
OUT.mkdir(parents=True)
FILES = OUT / "exports"
FILES.mkdir()
shutil.copytree(REAL, OUT / "test-333-project-copy")

app = create_application(["final-walkthrough-families"])
QSettings.setDefaultFormat(QSettings.Format.IniFormat)
QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope, str(OUT / "settings"))
from packlab_studio.shell import StudioMainWindow  # noqa: E402

window = StudioMainWindow(
    diagnostics_root=OUT / "diagnostics", packaging_library_root=OUT / "library"
)
window.resize(1600, 980)
window.show()
checks: dict[str, object] = {}


def pump(seconds: float = 0.3) -> None:
    end = time.time() + seconds
    while time.time() < end:
        app.processEvents()
        time.sleep(0.02)


def shot(name: str) -> None:
    pump(0.4)
    window.grab().save(str(OUT / f"{name}.png"))
    print("screenshot", name)


def route(target: Route) -> None:
    nav = window.findChild(QListWidget, "packlab.navigation.routes")
    row = next(r for r in range(nav.count()) if nav.item(r).data(0x0100) == target.value)
    rect = nav.visualItemRect(nav.item(row))
    QTest.mouseClick(nav.viewport(), Qt.MouseButton.LeftButton, pos=rect.center())
    pump()
    assert window.route_stack.currentWidget() is window.route_stack.views[target], target


def click(widget) -> None:
    assert widget.isEnabled(), widget.objectName()
    QTest.mouseClick(widget, Qt.MouseButton.LeftButton)
    pump()


families = window.route_stack.views[Route.PACKAGE_FAMILIES]
exports = window.route_stack.views[Route.EXPORTS]


def choose(family: str, preset: str, source: str) -> None:
    families.family.setCurrentIndex(families.family.findData(family))
    families.preset.setCurrentText(preset)
    families.source.setCurrentIndex(families.source.findData(source))
    pump()


def export_part(label: str, part: str, formats=("step", "stl")) -> list[str]:
    families.part.setCurrentIndex(families.part.findData(part))
    click(families.export_button)  # -> Exports page with the Design Model source
    assert window.route_stack.currentWidget() is exports
    assert exports.selected_source_kind is ExportSourceKind.DESIGN_MODEL
    target = window.project_manager.layout.path("export") / label / part
    target.mkdir(parents=True, exist_ok=True)
    exports.destination_provider = lambda _kind, _initial: target
    written = []
    for fmt in formats:
        exports.format_selector.setCurrentIndex(exports.format_selector.findData(fmt))
        click(exports.export_button)
        status = exports.status.text()
        print(f"  export {label}/{part}.{fmt}: {status[:140]}")
        assert status.startswith("Export complete"), status
    shot(f"{label}-{part}-exports-page")
    for path in sorted(target.iterdir()):
        shutil.copy2(path, FILES / f"{label}--{path.name}")
        written.append(path.name)
    route(Route.PACKAGE_FAMILIES)
    return written


# ---------------------------------------------------------------- 1. real test-333 jar
window.choose_open_project_path = lambda: str(OUT / "test-333-project-copy")
window.open_project_action.trigger()
pump()
assert window.project_manager.current is not None
route(Route.MEASURE_DESIGN)
measure = window.route_stack.views[Route.MEASURE_DESIGN]
measure.owner_review.setChecked(True)
click(measure.fit_button)
print("fit:", measure.status.text())
click(measure.save_button)
print("save jar:", measure.status.text())
checks["jar_design_model"] = measure.project_design.text()
shot("01-test333-jar-design-model-saved")

route(Route.PACKAGE_FAMILIES)
choose("closure", "Screw cap sized from the container", "captured")
checks["closure_defaults"] = {k: s.value() for k, s in families.spins.items()}
shot("02-test333-closure-defaults")
click(families.create_button)
print("closure:", families.status.text())
design = families.design
assert design is not None, families.status.text()
checks["closure"] = {
    "status": families.status.text(),
    "details": families.details.text(),
    "model_revision": design.model.revision_id,
    "previous_revision": design.model.previous_revision_id,
    "scan_master": design.model.fitted_to_scan_master_revision_id,
    "parts": {p.name: [round(v, 2) for v in p.preview.preview_bounds] for p in design.parts},
}
shot("03-test333-screw-cap-assembly")
families.viewer.orbit(0.6, 0.35)
shot("04-test333-screw-cap-assembly-orbit")
families.show_closure.setChecked(False)
pump()
checks["closure_hidden_scene"] = not families.viewer.service.scene.get("cap").visible
shot("05-test333-closure-hidden")
families.show_closure.setChecked(True)
families.spins["cap_diameter"].setValue(families.spins["cap_diameter"].value() - 4.0)
click(families.replace_button)
checks["closure_replacement_on_real_scan"] = families.status.text()
print("replace:", families.status.text())
click(families.save_button)
checks["closure_saved"] = families.status.text()
print("save closure:", families.status.text())
record, _document = window.project_manager.selected_design_model()
checks["closure_record"] = {k: record.get(k) for k in ("revision_id", "parent_kind", "scan_master_revision_id", "previous_design_model_revision_id", "overall_dimensions_mm_unverified")}
shot("06-test333-closure-saved")
checks["closure_exports"] = export_part("test333-closure", "cap")
checks["closure_exports"] += export_part("test333-closure-container", "container", ("step",))

# ---------------------------------------------------------------- 2. presets (standalone)
window.choose_new_project_path = lambda: str(OUT / "presets-project")
window.new_project_action.trigger()
pump()
assert window.project_manager.current is not None
route(Route.PACKAGE_FAMILIES)
presets = (
    ("jerrycan", "5 L jerrycan", ("body", "cap")),
    ("trigger_pump", "500 ml trigger sprayer bottle", ("bottle", "head")),
    ("tube", "100 ml cosmetic tube", ("tube",)),
)
for index, (family, preset, parts) in enumerate(presets, start=7):
    choose(family, preset, "standalone")
    click(families.create_button)
    print(family, "create:", families.status.text())
    assert families.design is not None and families.design.family == family, families.status.text()
    families.viewer.orbit(0.5, 0.3)
    shot(f"{index:02d}a-{family}-created")
    first = families.spins[next(iter(families.spins))]
    first.setValue(first.value() + 10.0)
    click(families.apply_button)
    print(family, "edit:", families.status.text())
    click(families.save_button)
    print(family, "save:", families.status.text())
    record, document = window.project_manager.selected_design_model()
    checks[family] = {
        "details": families.details.text(),
        "record_parent_kind": record["parent_kind"],
        "standalone_root": record["standalone_root_revision_id"],
        "previous": record["previous_design_model_revision_id"],
        "dimensions": record["overall_dimensions_mm_unverified"],
        "source_kind": document["model"]["parent_authority"]["source_kind"],
        "parts": {p.name: [round(v, 2) for v in p.preview.preview_bounds] for p in families.design.parts},
        "exports": [],
    }
    shot(f"{index:02d}b-{family}-saved")
    for part in parts:
        checks[family]["exports"] += export_part(family, part)

route(Route.LABELS)
checks["labels_with_family_selected"] = window.route_stack.views[Route.LABELS].status.text()
print("labels:", checks["labels_with_family_selected"])
shot("09c-labels-with-tube-selected")
route(Route.PACKAGE_FAMILIES)
choose("pouch", "Sachet 80 x 120 mm", "standalone")
click(families.create_button)
artwork = OUT / "synthetic-sachet-artwork.svg"
artwork.write_text(
    '<svg xmlns="http://www.w3.org/2000/svg" width="80" height="120" viewBox="0 0 80 120">'
    '<rect width="80" height="120" fill="#f4e3c1"/><circle cx="40" cy="45" r="22" fill="#c0392b"/>'
    '<rect x="10" y="85" width="60" height="12" fill="#1e8449"/></svg>',
    encoding="utf-8",
)
families._choose_artwork = lambda _parent: str(artwork)
click(families.artwork_button)
click(families.save_button)
checks["pouch"] = {"status": families.status.text(), "details": families.details.text(), "export_enabled": families.export_button.isEnabled()}
shot("10-sachet-artwork-saved")


# ---------------------------------------------------------------- 3. inspect exported files
def step_facts(path: Path) -> dict[str, object]:
    from OCP.Bnd import Bnd_Box
    from OCP.BRepBndLib import BRepBndLib
    from OCP.STEPControl import STEPControl_Reader

    text = path.read_text("utf-8", errors="replace")
    reader = STEPControl_Reader()
    reader.ReadFile(str(path))
    reader.TransferRoots()
    box = Bnd_Box()
    BRepBndLib.AddOptimal_s(reader.OneShape(), box, False, False)
    x0, y0, z0, x1, y1, z1 = box.Get()
    return {
        "header": text.splitlines()[0],
        "product": re.findall(r"PRODUCT\('([^']*)'", text)[:1],
        "length_unit": sorted(set(re.findall(r"SI_UNIT\(\.MILLI\.,\.METRE\.\)", text))),
        "size_mm": [round(x1 - x0, 2), round(y1 - y0, 2), round(z1 - z0, 2)],
    }


def stl_facts(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    count = struct.unpack("<I", data[80:84])[0]
    xs, ys, zs = [], [], []
    for index in range(count):
        offset = 84 + index * 50 + 12
        for vertex in range(3):
            x, y, z = struct.unpack("<fff", data[offset + vertex * 12 : offset + vertex * 12 + 12])
            xs.append(x)
            ys.append(y)
            zs.append(z)
    return {
        "triangles": count,
        "bytes": len(data),
        "size_mm": [round(max(xs) - min(xs), 2), round(max(ys) - min(ys), 2), round(max(zs) - min(zs), 2)],
    }


inspected = {}
for path in sorted(FILES.iterdir()):
    if path.suffix == ".step":
        inspected[path.name] = step_facts(path)
    elif path.suffix == ".stl":
        inspected[path.name] = stl_facts(path)
checks["exported_files"] = inspected
(OUT / "checks.json").write_text(json.dumps(checks, indent=2, default=str), encoding="utf-8")
print(json.dumps(inspected, indent=2))
window.close()
pump()
sys.exit(0)
