"""PL-0447/PL-0456 real-window drive: Design Model authority, undo/redo, autosave, crash recovery.

Usage (from the PackLab checkout):
  QT_QPA_PLATFORM=offscreen QT_QPA_FONTDIR=C:\\Windows\\Fonts uv run python <this file>
The orchestrator runs phase A in a child process, KILLS it (taskkill /F) after the autosave,
then starts phase B (recovery dialog on start) and phase C (clean reopen).
Everything lives under studio-e2e-history\\ (owner AppData untouched).
"""

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

WORK = Path(r"<USERPROFILE>\Documents\PackLab-work")
OUT = WORK / "studio-e2e-history"
MODEL = WORK / "test-333" / "mvs" / "scene_dense.ply"
PROJECT = OUT / "project"
FLAG = OUT / "phase-a-autosaved.flag"


def orchestrate() -> int:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    child = subprocess.Popen([sys.executable, __file__, "A"])
    deadline = time.time() + 900
    while not FLAG.exists():
        if child.poll() is not None or time.time() > deadline:
            print("phase A ended before autosave", child.returncode)
            return 1
        time.sleep(0.5)
    subprocess.run(["taskkill", "/F", "/PID", str(child.pid)], check=True)  # the "crash"
    child.wait()
    session = json.loads((PROJECT / "recovery" / "session.json").read_text(encoding="utf-8"))
    print("after kill, recovery marker:", session)
    for phase in ("B", "C"):
        result = subprocess.run([sys.executable, __file__, phase])
        if result.returncode:
            return result.returncode
    return 0


def window_phase(phase: str) -> int:
    from PySide6.QtCore import QSettings
    from PySide6.QtWidgets import QListWidget

    from packlab_studio.app import create_application
    from packlab_studio.navigation import Route

    app = create_application([f"studio-e2e-history-{phase}"])
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    QSettings.setPath(
        QSettings.Format.IniFormat, QSettings.Scope.UserScope, str(OUT / "settings")
    )
    from packlab_studio.shell import AUTOSAVE_DRAFT_JOB, StudioMainWindow

    window = StudioMainWindow(
        diagnostics_root=OUT / "diagnostics", packaging_library_root=OUT / "library"
    )
    window.resize(1500, 950)
    window.show()
    view = window.route_stack.views[Route.MEASURE_DESIGN]
    log_path = OUT / f"e2e_log_{phase}.json"
    log: dict[str, object] = {}

    def pump(seconds: float = 0.3) -> None:
        end = time.time() + seconds
        while time.time() < end:
            app.processEvents()
            time.sleep(0.02)

    def shot(name: str, widget=None) -> None:
        pump(0.4)
        (widget or window).grab().save(str(OUT / f"{name}.png"))
        entry = {
            "title": window.windowTitle().replace("[*]", "*" if window.isWindowModified() else ""),
            "status": view.status.text(),
            "project_design": view.project_design.text(),
            "save_indicator": window.save_indicator.text(),
            "statusbar": window.statusBar().currentMessage(),
            "undo_enabled": window.undo_action.isEnabled(),
            "redo_enabled": window.redo_action.isEnabled(),
        }
        log[name] = entry
        print(f"== {name}: {json.dumps(entry, ensure_ascii=False)}")
        log_path.write_text(json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8")

    def go_measure() -> None:
        nav = window.findChild(QListWidget, "packlab.navigation.routes")
        row = next(
            r for r in range(nav.count()) if nav.item(r).data(0x0100) == Route.MEASURE_DESIGN.value
        )
        nav.setCurrentRow(row)

    def current_design() -> str | None:
        selected = window.project_manager.selected_design_model()
        return None if selected is None else selected[0]["revision_id"]

    if phase == "A":
        window.new_project(PROJECT, "test-333 taft jar")
        go_measure()
        view._choose_file = lambda _parent: str(MODEL)
        view.open_button.click()
        view.isolate_button.click()
        view.bar_mm.setValue(98.0)
        view.marker_button.click()
        view.measure_button.click()
        view.promote_button.click()
        view.owner_review.setChecked(True)
        view.fit_button.click()
        if view.design is None:
            print("fit failed:", view.status.text())
            return 1
        view.height_mm.setValue(round(view.design.height + 5.0, 2))
        view.diameter_mm.setValue(round(view.design.diameter - 4.0, 2))
        view.apply_button.click()
        shot("A01-edited-unsaved-dirty")
        view.save_button.click()
        first = current_design()
        shot("A02-saved-design-model-is-project-current")
        view.height_mm.setValue(round(view.design.height + 2.0, 2))
        view.apply_button.click()
        view.save_button.click()
        second = current_design()
        shot("A03-second-revision-saved")
        window.undo_action.trigger()
        log["after_undo"] = current_design()
        shot("A04-edit-undo-back-to-first")
        window.redo_action.trigger()
        log["after_redo"] = current_design()
        shot("A05-edit-redo-second-again")
        window.close_project()
        window.open_project(PROJECT)
        go_measure()
        log["after_reopen"] = current_design()
        log["revisions"] = {"first": first, "second": second}
        shot("A06-close-reopen-design-model-still-current")
        # Unsaved edit -> autosave timer (2 s) -> crash.
        view.fit_button.click()
        view.height_mm.setValue(round(view.design.height + 7.0, 2))
        view.apply_button.click()
        log["unsaved_draft_height"] = view.design.height
        pump(3.0)
        shot("A07-autosaved-unsaved-edits-before-crash")
        log["checkpoint"] = json.loads(
            (PROJECT / "recovery" / "session.json").read_text(encoding="utf-8")
        )
        log_path.write_text(json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8")
        FLAG.write_text("ready", encoding="utf-8")
        while True:  # wait to be killed
            pump(1.0)
    if phase == "B":
        window.open_project(PROJECT)
        pump(0.5)
        dialog = window.recovery_dialog
        log["recovery_items"] = [
            [item.job_id, item.status.value, item.reason] for item in window.recovery_items
        ]
        if dialog is None or not dialog.isVisible():
            print("no recovery dialog")
            return 1
        shot("B01-recovery-dialog-window")
        shot("B02-recovery-dialog", dialog)
        dialog.buttons[AUTOSAVE_DRAFT_JOB][0].click()
        go_measure()
        log["restored_height"] = None if view.design is None else view.design.height
        shot("B03-draft-recovered-unsaved")
        box = window.show_portability_report()
        if box is None:
            return 1
        log["portability"] = {"text": box.text(), "info": box.informativeText()}
        shot("B04-portability-report", box)
        box.close()
        window.close()  # clean close
        pump(0.5)
        return 0
    if phase == "C":
        window.open_project(PROJECT)
        go_measure()
        pump(0.5)
        log["recovery_dialog_shown"] = window.recovery_dialog is not None
        log["current_design"] = current_design()
        shot("C01-clean-restart-no-recovery-design-current")
        window.close()
        return 0
    return 2


if __name__ == "__main__":
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    os.environ.setdefault("QT_QPA_FONTDIR", r"C:\Windows\Fonts")
    sys.exit(window_phase(sys.argv[1]) if len(sys.argv) > 1 else orchestrate())
