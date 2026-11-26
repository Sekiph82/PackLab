"""Drive the real StudioMainWindow offscreen through Measure & Design on test-333.

Usage (from the PackLab checkout):
  QT_QPA_PLATFORM=offscreen QT_QPA_FONTDIR=C:\\Windows\\Fonts uv run python <this file>
Owner AppData/registry stay untouched: library, diagnostics, settings and the project live
under studio-e2e-measure\\.
"""

import json
import shutil
import sys
import time
from pathlib import Path

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QListWidget

from packlab_studio.app import create_application
from packlab_studio.navigation import Route

WORK = Path(r"<USERPROFILE>\Documents\PackLab-work")
OUT = WORK / "studio-e2e-measure"
MODEL = WORK / "test-333" / "mvs" / "scene_dense.ply"
if OUT.exists():
    shutil.rmtree(OUT)
OUT.mkdir(parents=True)

app = create_application(["studio-e2e-measure"])
QSettings.setDefaultFormat(QSettings.Format.IniFormat)
QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope, str(OUT / "settings"))
from packlab_studio.shell import StudioMainWindow  # noqa: E402

window = StudioMainWindow(
    diagnostics_root=OUT / "diagnostics", packaging_library_root=OUT / "library"
)
window.resize(1500, 950)
window.show()
log: dict[str, object] = {"model": str(MODEL)}


def pump(seconds: float = 0.3) -> None:
    end = time.time() + seconds
    while time.time() < end:
        app.processEvents()
        time.sleep(0.02)


def shot(name: str) -> None:
    pump(0.4)
    window.grab().save(str(OUT / f"{name}.png"))
    log[name] = {"status": view.status.text(), "results": view.results.text()}
    print(f"== {name}\n   status: {view.status.text()}\n   results: {view.results.text()}")


window.new_project(OUT / "project", "test-333 taft jar")  # File menu lands in PR feat/studio-build-model
nav = window.findChild(QListWidget, "packlab.navigation.routes")
row = next(r for r in range(nav.count()) if nav.item(r).data(0x0100) == Route.MEASURE_DESIGN.value)
nav.setCurrentRow(row)
view = window.route_stack.views[Route.MEASURE_DESIGN]
assert window.route_stack.currentWidget() is view

view._choose_file = lambda _parent: str(MODEL)
view.open_button.click()
shot("01-open-built-model")
view.isolate_button.click()
shot("02-object-only")
view.bar_mm.setValue(98.0)  # owner's first print: the 100 mm bar measures ~98 mm
view.marker_button.click()
shot("03-scale-from-mat-markers")
view.measure_button.click()
shot("04-measurements-mm")
view._choose_save = lambda _parent, name: str(OUT / "dimension-report.json")
view.report_button.click()
shot("05-dimension-report-exported")
view.promote_button.click()
shot("06-scan-master-promoted")
view.fit_button.click()
shot("07-fit-without-owner-review")
view.owner_review.setChecked(True)
view.fit_button.click()
shot("08-design-model-fitted-overlay")
if view.design is not None:
    view.height_mm.setValue(round(view.design.height + 5.0, 2))
    view.diameter_mm.setValue(round(view.design.diameter - 4.0, 2))
    view.apply_button.click()
    shot("09-design-model-edited")
    view.save_button.click()
    shot("10-design-model-saved")
view.viewer.orbit(0, 35)
shot("11-overlay-orbited")

measurements = view.measurements
log["measured_mm_unverified"] = (
    {item.name: [item.value_mm, item.report.propagated_standard_uncertainty] for item in measurements.dimensions}
    if measurements
    else None
)
log["scale"] = (
    {
        "source": view.scale.source,
        "mm_per_unit": view.scale.mm_per_unit,
        "uncertainty": view.scale.uncertainty,
        "details": view.scale.details,
    }
    if view.scale
    else None
)
log["scan_master"] = view.scan_master.revision_id if view.scan_master else None
log["design"] = view.design.as_dict()["overall_dimensions_mm_unverified"] if view.design else None
log["design_saved"] = str(view.saved_design_path) if view.saved_design_path else None
(OUT / "e2e_log.json").write_text(json.dumps(log, indent=2, default=str), encoding="utf-8")
window.close()
sys.exit(0 if view.design is not None else 1)
