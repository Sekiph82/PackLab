"""Real PL-0443/PL-0453 check: drive the real StudioMainWindow offscreen, import the owner's
Test-333 package, let the automatic Build model run with the real COLMAP/OpenMVS engines,
and save window screenshots (import, progress, finished model in the viewer).

Isolated data roots under OUT/data so the owner's real AppData inbox/project stay untouched.
Run from the PackLab checkout:  uv run --locked python <this file>
"""

import os
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QPA_FONTDIR", r"C:\Windows\Fonts")  # offscreen has no fonts otherwise

from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402

from packlab_studio.app import create_application  # noqa: E402
from packlab_studio.build_model import BuildModelView  # noqa: E402
from packlab_studio.capture_inbox import CaptureInboxView  # noqa: E402
from packlab_studio.model_viewer import ModelViewerView  # noqa: E402
from packlab_studio.navigation import Route  # noqa: E402
from packlab_studio.receiver_session import ReceiverSession  # noqa: E402
from packlab_studio.shell import StudioMainWindow  # noqa: E402

OUT = Path(r"<USERPROFILE>\Documents\PackLab-work\pl0463-repeat")
DATA = OUT / time.strftime("data-%Y%m%d-%H%M%S")  # fresh isolated root per run
PACKAGE = Path(r"<USERPROFILE>\Documents\PackLab-work\test-333\test-333-import.packscan")
DATA.mkdir(parents=True)

app = create_application(["studio-e2e-build"])
window = StudioMainWindow(
    receiver_session_factory=lambda: ReceiverSession(
        DATA / "transfer-inbox", tls_root=DATA / "transfer-tls", port=0
    ),
    diagnostics_root=DATA / "diagnostics",
    packaging_library_root=DATA / "library",
    default_project_root=DATA / "projects" / "default",
    settings_path=DATA / "studio-settings.ini",
)
window.resize(1400, 900)
window.show()


def pump(seconds: float = 0.3) -> None:
    end = time.time() + seconds
    while time.time() < end:
        app.processEvents()
        time.sleep(0.02)


def shot(name: str) -> None:
    pump(0.3)
    window.grab().save(str(OUT / f"{name}.png"))
    print(time.strftime("%H:%M:%S"), "screenshot", name, flush=True)


inbox = window.route_stack.views[Route.CAPTURE_INBOX]
builds = window.route_stack.views[Route.RECONSTRUCTION]
viewer = window.route_stack.views[Route.MODEL_VIEWER]
assert isinstance(inbox, CaptureInboxView) and isinstance(builds, BuildModelView)
assert isinstance(viewer, ModelViewerView)
print("project:", window.project_manager.current)
window.navigation.navigate(Route.CAPTURE_INBOX)
shot("01-capture-inbox-default-project")

started = time.monotonic()
inbox._choose_file = lambda parent: str(PACKAGE)
QTest.mouseClick(inbox.import_button, Qt.MouseButton.LeftButton)
print("import status:", inbox.status_label.text().replace("\n", " | "))
window.navigation.navigate(Route.CAPTURE_INBOX)
shot("02-imported-build-queued")
window.navigation.navigate(Route.RECONSTRUCTION)

jobs = window.job_manager.jobs()
assert jobs, "automatic Build model did not queue a job"
job_id = jobs[0].job_id
last = ""
index = 3
while builds.result is None:
    pump(1.0)
    message = window.job_manager.get(job_id).message
    if message != last:
        last = message
        print(time.strftime("%H:%M:%S"), f"[{time.monotonic() - started:.0f}s]", message, flush=True)
        window.navigation.navigate(Route.RECONSTRUCTION)
        shot(f"{index:02d}-progress-{message.split(' ', 1)[0].replace('/', 'of')}")
        index += 1
    if time.monotonic() - started > 3600:
        raise SystemExit("build did not finish within an hour")

result = builds.result
print("result:", result.status, result.message)
print("registered:", result.registered_images, "of", result.input_images, "seconds:", round(result.seconds))
print("model:", result.model_path, "textured:", result.textured_mesh_path)
print("job:", window.job_manager.get(job_id).state, window.job_manager.get(job_id).error)
pump(1.0)
window.navigation.navigate(Route.RECONSTRUCTION)
shot(f"{index:02d}-build-finished-next-steps")
window.navigation.navigate(Route.MODEL_VIEWER)
shot(f"{index + 1:02d}-model-viewer-finished")
viewer.orbit(60, 25)
shot(f"{index + 2:02d}-model-viewer-orbit")
print("viewer status:", viewer.status.text())
window.close()
pump(1.0)
print("done; total", round(time.monotonic() - started), "s")
