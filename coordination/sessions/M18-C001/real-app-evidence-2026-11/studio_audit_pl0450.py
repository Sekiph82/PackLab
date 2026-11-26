"""PL-0450 real-window audit: drive production StudioMainWindow() offscreen, click everything."""
import json, sys, tempfile, time, traceback
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import (QAbstractButton, QComboBox, QDockWidget, QLabel, QLineEdit,
                               QListWidget, QMenuBar, QToolBar, QWidget)
from packlab_studio.app import create_application
from packlab_studio.shell import StudioMainWindow

OUT = Path(r"<USERPROFILE>\Documents\PackLab-work\studio-audit"); OUT.mkdir(parents=True, exist_ok=True)
TMP = Path(tempfile.mkdtemp(prefix="pl0450-"))
errors = []
def _hook(t, v, tb):
    s = "".join(traceback.format_exception(t, v, tb)); errors.append(s); print("EXC", s, flush=True)
sys.excepthook = _hook
app = create_application(["pl0450-audit"])
# Same constructor as app.run(); only redirect the library/diagnostic roots away from owner AppData.
window = StudioMainWindow(packaging_library_root=TMP / "library", diagnostics_root=TMP / "diag")
window.resize(1400, 900); window.show()
log = {"tmp": str(TMP)}

def pump(s=0.3):
    end = time.time() + s
    while time.time() < end: app.processEvents(); time.sleep(0.02)

def shot(name):
    pump(); p = OUT / f"{name}.png"; window.grab().save(str(p)); return str(p)

nav = window.findChild(QListWidget, "packlab.navigation.routes")
nav_log = []

def routes():
    return [(nav.item(r).text(), bool(nav.item(r).flags() & Qt.ItemFlag.ItemIsEnabled)) for r in range(nav.count())]

def go(label):
    for r in range(nav.count()):
        if nav.item(r).text() == label:
            QTest.mouseClick(nav.viewport(), Qt.MouseButton.LeftButton, pos=nav.visualItemRect(nav.item(r)).center())
            pump()
            from packlab_studio.navigation import Route
            want = window.route_stack.views[Route(nav.item(r).data(0x0100))]
            reached = window.route_stack.currentWidget() is want
            nav_log.append((label, reached))
            return want
    raise KeyError(label)

def describe(view):
    return {"class": type(view).__name__, "enabled": view.isEnabled(),
            "buttons": [(b.text(), b.isEnabled()) for b in view.findChildren(QAbstractButton) if b.text()],
            "labels": [l.text()[:300] for l in view.findChildren(QLabel) if l.text()] + ([view.text()] if isinstance(view, QLabel) else []),
            "combos": [[c.itemText(i) for i in range(c.count())] for c in view.findChildren(QComboBox)]}

def click(view, text):
    for b in view.findChildren(QAbstractButton):
        if b.text() == text:
            en = b.isEnabled(); QTest.mouseClick(b, Qt.MouseButton.LeftButton); pump(); return en
    return None

log["menubar_actions"] = [a.text() for a in window.menuBar().actions()] if window.findChild(QMenuBar) else []
log["toolbars"] = [t.windowTitle() for t in window.findChildren(QToolBar)]
log["docks"] = {d.windowTitle(): (type(d.widget()).__name__, d.isVisible(), d.widget().text() if isinstance(d.widget(), QLabel) else "") for d in window.findChildren(QDockWidget)}

def audit_all(phase):
    out = {"routes": routes()}
    for label, _ in routes():
        v = go(label); key = label.replace(" ", "-").lower()
        out[label] = describe(v); out[label]["shot"] = shot(f"{phase}-{key}")
    # click real buttons
    lib = go("Library")
    out["lib_refresh"] = click(lib, "Refresh"); out["lib_clear"] = click(lib, "Clear filters")
    out["lib_create_sku_enabled"] = click(lib, "Create SKU from selected geometry")
    out["lib_after"] = [l.text() for l in lib.findChildren(QLabel) if l.objectName() in ("packlab.library.selection", "packlab.library.state-message")]
    out["lib_click_shot"] = shot(f"{phase}-library-after-clicks")
    mc = go("Mask Correction")
    out["mask_buttons_enabled"] = {t: click(mc, t) for t in ("Undo", "Submit correction", "Cancel")}
    out["mask_status"] = mc.status.text()
    ed = go("Editor")
    out["editor_promote_empty"] = click(ed, "Promote to Scan Master"); out["editor_status_empty"] = ed.status.text()
    ed.actor_input.setText("owner"); ed.reason_input.setText("audit")
    click(ed, "Promote to Scan Master"); out["editor_status_filled"] = ed.status.text()
    out["editor_shot"] = shot(f"{phase}-editor-after-promote")
    ex = go("Exports")
    for i in range(ex.source_selector.count()):
        ex.source_selector.setCurrentIndex(i); pump()
        en = click(ex, "Export selected source")
        out[f"export_src{i}"] = {"source": ex.source_selector.itemText(i), "summary": ex.source_summary.text(),
                                 "formats": ex.available_formats.text(), "button_enabled": en, "status": ex.status.text(),
                                 "shot": shot(f"{phase}-exports-src{i}")}
    out["nav_reached"] = list(nav_log); nav_log.clear()
    return out

log["no_project"] = audit_all("A-noproject")
# (d) probe: project via the programmatic API only (no UI exists for New/Open).
try:
    window.new_project(TMP / "proj", "pl0450-audit"); pump()
    log["project_created_via_api"] = True
    log["with_project"] = audit_all("B-api-project")
except Exception:
    log["project_created_via_api"] = traceback.format_exc()
log["dock_texts_after"] = {d.windowTitle(): (d.isVisible(), d.widget().text() if isinstance(d.widget(), QLabel) else type(d.widget()).__name__) for d in window.findChildren(QDockWidget)}
log["uncaught_errors"] = errors
window.close(); pump(0.5)
(OUT / "audit_log.json").write_text(json.dumps(log, indent=1, default=str))
print(json.dumps(log, indent=1, default=str))
