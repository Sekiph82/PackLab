"""Real-app defects found by clicking the Desktop PackLab.exe under pythonw (M20-S05 round 1)."""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import uuid
from pathlib import Path

import pytest

from packlab_studio import app as studio_app
from packlab_studio import navigation
from packlab_studio import version as studio_version
from packlab_studio.project import ProjectManager
from packlab_studio.project_layout import ProjectLayout, ProjectLayoutError

windows_only = pytest.mark.skipif(os.name != "nt", reason="Windows junctions and mutexes")


def test_f1_missing_pythonw_streams_go_to_a_log_file(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(sys, "stdout", None)
    monkeypatch.setattr(sys, "stderr", None)
    monkeypatch.setattr(studio_app.faulthandler, "enable", lambda file: None)
    target = studio_app.install_windowed_streams(tmp_path / "logs")
    try:
        assert target == tmp_path / "logs" / "studio.log"
        print("library progress line")  # what Open3D's logger does under pythonw
        sys.stderr.write("warning line\n")
        sys.stdout.flush()
        text = target.read_text(encoding="utf-8")
        assert "library progress line" in text and "warning line" in text
    finally:
        sys.stdout.close()


def test_f1_console_streams_are_left_alone(tmp_path) -> None:
    assert studio_app.install_windowed_streams(tmp_path) is None
    assert not (tmp_path / "studio.log").exists()


def _project(tmp_path: Path) -> Path:
    root = tmp_path / "real" / "projects" / "default"
    ProjectManager().new_project(root, "My scans")
    return root


@windows_only
def test_f2_project_reached_through_a_junction_opens(tmp_path) -> None:
    _project(tmp_path)
    link = tmp_path / "redirected"
    subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(link), str(tmp_path / "real")],
        check=True,
        capture_output=True,
    )
    root = link / "projects" / "default"
    layout = ProjectLayout.open(root)
    assert layout.path("working", "project.json") == root / "working" / "project.json"
    assert ProjectManager().open_project(root).name == "My scans"


@windows_only
def test_f2_junction_inside_an_area_is_still_rejected(tmp_path) -> None:
    root = _project(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(root / "working" / "escape"), str(outside)],
        check=True,
        capture_output=True,
    )
    with pytest.raises(ProjectLayoutError, match="link"):
        ProjectLayout.open(root).path("working", "escape/secret.json")


def test_f2_redirected_resolve_does_not_block_open(monkeypatch, tmp_path) -> None:
    root = _project(tmp_path)
    original = pathlib.Path.resolve
    redirected = tmp_path / "msix-virtual"

    def fake_resolve(self: Path, strict: bool = False) -> Path:  # MSIX/OneDrive redirection
        resolved = original(self, strict=strict)
        try:
            return redirected / resolved.relative_to(tmp_path)
        except ValueError:
            return resolved

    monkeypatch.setattr(pathlib.Path, "resolve", fake_resolve)
    assert ProjectManager().open_project(root).name == "My scans"
    with pytest.raises(ProjectLayoutError):
        ProjectLayout.open(root).path("working", "..\\..\\secret")


@windows_only
def test_f3_second_instance_is_detected_and_first_window_file_round_trips(tmp_path) -> None:
    name = f"packlab-test-{uuid.uuid4().hex}"
    first = studio_app.claim_single_instance(name)
    assert first  # a real mutex handle
    assert studio_app.claim_single_instance(name) is None
    assert not studio_app.activate_running_instance(tmp_path / "missing.txt")
    stale = tmp_path / "instance-window.txt"
    stale.write_text("0", encoding="ascii")
    assert not studio_app.activate_running_instance(stale)  # not a window: nothing to focus


def test_f5_maximized_window_saves_normal_geometry_and_restores_on_screen(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from packlab_studio.app import create_application
    from packlab_studio.preferences import PreferencesStore, WindowPreferences
    from packlab_studio.shell import StudioMainWindow

    app = create_application(["packlab-f5"])
    store = PreferencesStore(tmp_path / "preferences.json")
    store.save(WindowPreferences(geometry=(1500, -30, 1280, 800), maximized=True))
    window = StudioMainWindow(preferences=store, available_work_area=(0, 0, 1920, 1040))
    assert window.isMaximized()
    window.close()
    app.processEvents()
    saved = store.load()
    x, y, width, height = saved.geometry
    assert saved.maximized
    assert y >= 40 and x + width <= 1920 - 8 and y + height <= 1040 - 8  # title bar visible


def test_f15_dialogs_start_in_documents_packlab_then_last_folder(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from packlab_studio import shell
    from packlab_studio.app import create_application
    from packlab_studio.shell import StudioMainWindow

    app = create_application(["packlab-f15"])
    monkeypatch.setattr(shell, "documents_folder", lambda: tmp_path / "Documents" / "PackLab")
    window = StudioMainWindow(
        diagnostics_root=tmp_path / "diagnostics",
        packaging_library_root=tmp_path / "library",
        settings_path=tmp_path / "settings.ini",
    )
    try:
        assert window.dialog_folder() == tmp_path / "Documents" / "PackLab"
        chosen = tmp_path / "work" / "Bottle"
        chosen.parent.mkdir()
        window.choose_new_project_path = lambda: str(chosen)
        window.new_project_action.trigger()
        assert window.dialog_folder() == chosen.parent  # beside the open project
        window.close_project()
        assert window.dialog_folder() == chosen.parent  # remembered
    finally:
        window.close()
        app.processEvents()


def test_f11_ownerdev_manifest_supplies_build_revision(monkeypatch, tmp_path) -> None:
    commit = "a" * 40
    manifest = tmp_path / "owner-dev-runtime.json"
    manifest.write_text(json.dumps({"source_commit": commit}), encoding="utf-8")
    monkeypatch.delenv("PACKLAB_BUILD_REVISION", raising=False)
    monkeypatch.setattr(studio_version, "packlab_data_root", lambda: tmp_path / "none")
    monkeypatch.setattr(studio_version, "OWNERDEV_RUNTIME_MANIFEST", manifest)
    assert studio_version.current_build_info().build_revision == commit
    manifest.unlink()
    monkeypatch.setenv("PACKLAB_OWNERDEV_SOURCE_SHA", "b" * 40)
    assert studio_version.current_build_info().build_revision == "b" * 40


def test_f11_every_openmvs_tool_is_probed_or_says_version_not_reported(monkeypatch) -> None:
    from packlab_core.engine_probe import EngineProbeResult, EngineProbeStatus, EngineVersion
    from packlab_studio.engine_config import (
        DiscoveryStatus,
        EngineDiscoveryReport,
        EnginePathDiagnostic,
    )

    report = EngineDiscoveryReport(
        tuple(
            EnginePathDiagnostic(
                engine_id, Path(f"C:/e/{engine_id}.exe"), "bundled", DiscoveryStatus.CONFIGURED, ""
            )
            for engine_id in ("openmvs.densify_point_cloud", "openmvs.texture_mesh")
        )
    )
    monkeypatch.setattr(navigation, "discover_engines", lambda: report)
    versions = iter((EngineVersion(2, 3, 0), None))

    def fake(executable: Path, *, runner: object) -> EngineProbeResult:
        version = next(versions)
        status = EngineProbeStatus.VALID if version else EngineProbeStatus.INVALID
        return EngineProbeResult("openmvs", str(executable), status, version, "")

    monkeypatch.setattr(navigation, "probe_openmvs", fake)
    rows = navigation.engine_rows(probe=True)
    assert "version 2.3.0 (valid)" in rows[0]
    assert "version not reported" in rows[1]


def test_f3_second_launch_focuses_first_and_exits_with_already_running(monkeypatch) -> None:
    focused: list[bool] = []
    monkeypatch.setattr(studio_app, "create_application", lambda _argv: object())
    monkeypatch.setattr(studio_app, "claim_single_instance", lambda: None)
    monkeypatch.setattr(studio_app, "activate_running_instance", lambda: focused.append(True))
    monkeypatch.setattr(studio_app, "StudioMainWindow", lambda **_kw: pytest.fail("no window"))
    assert studio_app.run(["PackLabStudio"]) == studio_app.EXIT_ALREADY_RUNNING == 75
    assert focused == [True]
    tools = Path(__file__).resolve().parents[2] / "tools" / "dev"
    launcher = (tools / "PackLabOwnerLauncher.cs").read_text(encoding="utf-8")
    script = (tools / "launch_owner_packlab.ps1").read_text(encoding="utf-8")
    main = (Path(studio_app.__file__).parent / "__main__.py").read_text(encoding="utf-8")
    assert "AlreadyRunningExitCode = 75;" in launcher and "-eq 75) { exit 0 }" in script
    assert "_exit_code != EXIT_ALREADY_RUNNING" in main
    # abort()/qFatal exit 3: still a startup failure everywhere (M1).
    assert "= 3;" not in launcher and "-eq 3)" not in script and "!= 3" not in main


_REJECTED = (
    "/x",
    r"\x",
    "/Users/escape/ESCAPED.txt",
    r"\server\share\x",
    r"\\server\share\x",
    "//server/share/x",
    r"\\?\C:\x",
    r"\\.\PhysicalDrive0",
    "//?/C:/x",
    "C:x",
    r"C:\x",
    "c:/x",
    "a.json:stream",
    "dir/a.json::$DATA",
    "..",
    "a/../../x",
    r"..\x",
    ".. ",
    "...",
    ". .",
    "a/b.",
    "a/b ",
    "CON",
    "con.txt",
    "dir/NUL",
    "PRN.json",
    "AUX.tar.gz",
    "COM1",
    "com9.log",
    "LPT1.txt",
    "lpt9",
    "COM\u00b9",
    "CON .txt",
    "CONIN$",
    "",
)


@pytest.mark.parametrize("value", _REJECTED)
def test_h1_m2_unsafe_relative_paths_are_rejected(value: str) -> None:
    from packlab_studio.project_layout import safe_relative_path

    with pytest.raises(ProjectLayoutError):
        safe_relative_path(value)


def test_h1_safe_relative_paths_still_accepted() -> None:
    from packlab_studio.project_layout import safe_relative_path

    assert safe_relative_path("a/./b//c.json") == Path("a", "b", "c.json")
    assert safe_relative_path(r"autosave\design-model-draft.json") == Path(
        "autosave", "design-model-draft.json"
    )
    assert safe_relative_path("console.txt") == Path("console.txt")  # not a device name
    assert safe_relative_path(".packlab-layout.json") == Path(".packlab-layout.json")


def test_h1_reviewer_escape_call_is_refused(tmp_path) -> None:
    root = _project(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    layout = ProjectLayout.open(root)
    # The reviewer's call: a root-relative path ("/Users/.../ESCAPED.txt", no drive).
    escaped = (outside / "ESCAPED.txt").as_posix()
    rooted = "/" + escaped.split(":", 1)[-1].lstrip("/")
    for value in (rooted, rooted.replace("/", "\\"), str(outside / "ESCAPED.txt")):
        with pytest.raises(ProjectLayoutError):
            target = layout.path("working", value)
            target.write_text("escaped", encoding="utf-8")
    assert not (outside / "ESCAPED.txt").exists()


@windows_only
def test_l1_junction_at_the_area_itself_is_rejected(tmp_path) -> None:
    root = _project(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    (root / "cache").rmdir()
    subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(root / "cache"), str(outside)],
        check=True,
        capture_output=True,
    )
    with pytest.raises(ProjectLayoutError, match="link"):
        ProjectLayout.open(root).path("cache", "x.bin")
