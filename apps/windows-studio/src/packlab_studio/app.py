"""PackLab Studio application ownership and process boundary."""

from __future__ import annotations

import faulthandler
import getpass
import hashlib
import os
import sys
import tempfile
import traceback
from collections.abc import Sequence
from pathlib import Path

from PySide6.QtCore import QCoreApplication, QStandardPaths
from PySide6.QtWidgets import QApplication, QWidget

from .branding import application_icon, set_windows_app_user_model_id
from .frozen_runtime import safe_exception_summary
from .preferences import PreferencesStore, documents_folder
from .shell import StudioMainWindow

ORGANIZATION_NAME = "PackLab"
APPLICATION_NAME = "PackLab Studio"
EXIT_SUCCESS = 0
EXIT_STARTUP_FAILURE = 1
# PackLab was already running and its window was focused. Launchers treat only this code as
# success; it is not 3, which MSVC abort()/qFatal also return, so native crashes still fail.
EXIT_ALREADY_RUNNING = 75
BUILD_SMOKE_ARGUMENT = "--packlab-build-smoke"
LOG_ROTATE_BYTES = 5 * 1024 * 1024


def studio_log_dir() -> Path:
    """%LOCALAPPDATA%/PackLab/PackLab Studio/logs (same root as AppLocalDataLocation)."""

    base = os.environ.get("LOCALAPPDATA") or tempfile.gettempdir()
    return Path(base) / ORGANIZATION_NAME / APPLICATION_NAME / "logs"


def install_windowed_streams(log_dir: Path | None = None) -> Path | None:
    """Under pythonw sys.stdout/sys.stderr are None; any library write (Open3D's logger,
    print, warnings) then raises AttributeError inside the feature that triggered it (F1).
    Point missing streams at a size-rotated log file and keep faulthandler writing there."""

    if sys.stdout is not None and sys.stderr is not None:
        return None
    target = (log_dir or studio_log_dir()) / "studio.log"
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and target.stat().st_size > LOG_ROTATE_BYTES:
            os.replace(target, target.with_suffix(".log.1"))
        stream = open(target, "a", encoding="utf-8", errors="replace", buffering=1)  # noqa: SIM115
    except OSError:
        stream = open(os.devnull, "w", encoding="utf-8")  # noqa: SIM115
        target = Path(os.devnull)
    if sys.stdout is None:
        sys.stdout = stream
    if sys.stderr is None:
        sys.stderr = stream
    faulthandler.enable(file=stream)
    return target


ERROR_ALREADY_EXISTS = 183
SW_RESTORE = 9


def _instance_name() -> str:
    user = hashlib.sha256(getpass.getuser().encode("utf-8")).hexdigest()[:16]
    return f"packlab-studio-{user}"


def _instance_window_file() -> Path:
    return studio_log_dir().parent / "instance-window.txt"


def claim_single_instance(name: str | None = None) -> int | None:
    """Per-user named mutex: a handle (0 off Windows) for the first instance, None otherwise.

    The OS releases the mutex when the process exits, so a crash never blocks a relaunch (F3).
    """

    if os.name != "nt":
        return 0
    import ctypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateMutexW.restype = ctypes.c_void_p
    kernel32.CreateMutexW.argtypes = (ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p)
    kernel32.CloseHandle.argtypes = (ctypes.c_void_p,)
    handle = kernel32.CreateMutexW(None, False, "Local\\" + (name or _instance_name()))
    if handle and ctypes.get_last_error() == ERROR_ALREADY_EXISTS:
        kernel32.CloseHandle(handle)
        return None
    return int(handle or 0)


def publish_instance_window(window: QWidget, path: Path | None = None) -> None:
    try:
        target = path or _instance_window_file()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(str(int(window.winId())), encoding="ascii")
    except (OSError, ValueError):
        pass


def activate_running_instance(path: Path | None = None) -> bool:
    """Bring the first instance's window to the front; the new process owns the foreground
    right because the user just launched it, so SetForegroundWindow is permitted here."""

    if os.name != "nt":
        return False
    try:
        hwnd = int((path or _instance_window_file()).read_text(encoding="ascii").strip())
    except (OSError, ValueError):
        return False
    import ctypes

    user32 = ctypes.WinDLL("user32")
    user32.IsWindow.argtypes = user32.IsIconic.argtypes = (ctypes.c_void_p,)
    user32.ShowWindow.argtypes = (ctypes.c_void_p, ctypes.c_int)
    user32.SetForegroundWindow.argtypes = (ctypes.c_void_p,)
    if not user32.IsWindow(hwnd):
        return False
    if user32.IsIconic(hwnd):
        user32.ShowWindow(hwnd, SW_RESTORE)
    return bool(user32.SetForegroundWindow(hwnd))


def _write_ownerdev_startup_failure(error: Exception, *, enabled: bool) -> None:
    """Preserve a local traceback only for the explicit OWNER DEV source launcher."""

    log_path = os.environ.get("PACKLAB_OWNERDEV_STARTUP_LOG")
    if not enabled or not log_path:
        return
    try:
        Path(log_path).parent.mkdir(parents=True, exist_ok=True)
        Path(log_path).write_text(
            "PackLab OWNER DEV source startup exception\n"
            f"deployed_sha={os.environ.get('PACKLAB_OWNERDEV_SOURCE_SHA', 'unknown')}\n"
            f"studio_version={os.environ.get('PACKLAB_OWNERDEV_STUDIO_VERSION', 'unknown')}\n"
            f"exception_type={type(error).__name__}\n"
            f"exception_message={safe_exception_summary(error)}\n"
            "traceback:\n"
            f"{''.join(traceback.format_exception(type(error), error, error.__traceback__))}",
            encoding="utf-8",
        )
    except OSError:
        pass


def enter_documents_folder() -> None:
    """Qt file dialogs given no folder start in the working directory, which an Explorer
    launch leaves at the user home; make it Documents/PackLab instead (F15)."""

    sys.path[:] = [entry for entry in sys.path if entry not in ("", ".")]  # cwd is no import root
    try:
        os.chdir(documents_folder())
    except OSError:
        pass


def create_application(argv: Sequence[str] | None = None) -> QApplication:
    """Create the one process-owned QApplication without import-time side effects."""

    existing = QCoreApplication.instance()
    if existing is not None:
        if not isinstance(existing, QApplication):
            raise RuntimeError("PackLab Studio requires a QApplication instance")
        return existing
    set_windows_app_user_model_id()
    arguments = list(argv) if argv is not None else sys.argv
    app = QApplication(arguments)
    app.setOrganizationName(ORGANIZATION_NAME)
    app.setApplicationName(APPLICATION_NAME)
    app.setWindowIcon(application_icon())
    return app


def run(argv: Sequence[str] | None = None) -> int:
    """Start the shell and return a deterministic process exit code."""

    build_smoke = False
    install_windowed_streams()
    try:
        arguments = list(argv) if argv is not None else sys.argv.copy()
        build_smoke = BUILD_SMOKE_ARGUMENT in arguments
        if build_smoke:
            arguments.remove(BUILD_SMOKE_ARGUMENT)
        app = create_application(arguments)
        if build_smoke:  # must not create user projects or settings
            window = StudioMainWindow()
        else:
            if claim_single_instance() is None:
                activate_running_instance()
                return EXIT_ALREADY_RUNNING  # one PackLab per user; that window is in front
            enter_documents_folder()
            data_root = Path(
                QStandardPaths.writableLocation(
                    QStandardPaths.StandardLocation.AppLocalDataLocation
                )
                or Path.home() / ".packlab"
            )
            window = StudioMainWindow(
                default_project_root=data_root / "projects" / "default",
                settings_path=data_root / "studio-settings.ini",
                preferences=PreferencesStore(data_root / "window-preferences.json"),
            )
        window.show()
        if not build_smoke:
            publish_instance_window(window)
        if build_smoke:
            app.processEvents()
            from .build_smoke import run_frozen_capability_smoke

            run_frozen_capability_smoke()
            if not window.close():
                raise RuntimeError("StudioMainWindow refused to close during build smoke.")
            app.processEvents()
            app.quit()
            return EXIT_SUCCESS
        return int(app.exec())
    except Exception as error:
        if build_smoke:
            log_path = os.environ.get("PACKLAB_BUILD_SMOKE_LOG")
            if log_path:
                try:
                    Path(log_path).write_text(
                        "PackLab frozen capability smoke failed "
                        f"({type(error).__name__}): {safe_exception_summary(error)}\n",
                        encoding="utf-8",
                    )
                except OSError:
                    pass
        _write_ownerdev_startup_failure(
            error,
            enabled=os.name == "nt" and os.environ.get("PACKLAB_OWNERDEV_DIAGNOSTICS") == "1",
        )
        return EXIT_STARTUP_FAILURE


def main() -> int:
    return run()


if __name__ == "__main__":
    raise SystemExit(main())
