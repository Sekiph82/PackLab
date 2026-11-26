"""PL-0454/0455/0457 real-window check: default project, File menu, Engines panel screenshot."""

import os
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QPA_FONTDIR", r"C:\Windows\Fonts")
os.environ.setdefault("PACKLAB_COLMAP_PATH", r"<USERPROFILE>\Tools\colmap\bin\colmap.exe")
os.environ.setdefault("PACKLAB_OPENMVS_ROOT", r"<USERPROFILE>\Tools\openmvs\vc17\x64\Release")

from packlab_studio.app import create_application  # noqa: E402
from packlab_studio.navigation import Route, SettingsView  # noqa: E402
from packlab_studio.preferences import PreferencesStore  # noqa: E402
from packlab_studio.shell import StudioMainWindow  # noqa: E402

OUT = Path(r"<USERPROFILE>\Documents\PackLab-work\studio-e2e-build")
DATA = OUT / time.strftime("menus-%Y%m%d-%H%M%S")
DATA.mkdir(parents=True)
app = create_application(["studio-e2e-menus"])
window = StudioMainWindow(
    diagnostics_root=DATA / "diagnostics",
    packaging_library_root=DATA / "library",
    default_project_root=DATA / "projects" / "default",
    settings_path=DATA / "studio-settings.ini",
    preferences=PreferencesStore(DATA / "window-preferences.json"),
)
window.resize(1400, 900)
window.show()
app.processEvents()
print("menus:", [action.text() for action in window.menuBar().actions()])
print("file:", [a.text() for a in window.menuBar().actions()[0].menu().actions()])
print("title:", window.windowTitle())
settings = window.route_stack.views[Route.SETTINGS]
assert isinstance(settings, SettingsView)
window.navigation.navigate(Route.SETTINGS)
settings.recheck_button.click()
for _ in range(20):
    app.processEvents()
    time.sleep(0.02)
print("engines:", *[settings.engines.item(i).text() for i in range(settings.engines.count())], sep="\n  ")
window.grab().save(str(OUT / "20-settings-engines-recheck.png"))
window.diagnostic_bundle_action.trigger()
print("status:", window.statusBar().currentMessage())
window.close()
app.processEvents()
print("prefs saved:", (DATA / "window-preferences.json").read_text(encoding="utf-8")[:120])
