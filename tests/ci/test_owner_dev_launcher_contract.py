from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_production_spec_embeds_branding_asset_and_executable_icon() -> None:
    spec = (ROOT / "tools/packaging/packlab_studio.spec").read_text(encoding="utf-8")
    assert "icon=str(icon_path)" in spec
    assert 'str(branding_path), "apps/windows-studio/assets/branding"' in spec


def test_owner_scripts_use_stable_runtime_and_atomic_staging() -> None:
    deploy = (ROOT / "tools/dev/update_owner_dev_runtime.ps1").read_text(encoding="utf-8")
    launcher = (ROOT / "tools/dev/PackLabOwnerLauncher.cs").read_text(encoding="utf-8")
    bootstrap = (ROOT / "tools/dev/owner_packlab_bootstrap.py").read_text(encoding="utf-8")
    build = (ROOT / "tools/dev/build_owner_packlab_exe.ps1").read_text(encoding="utf-8")
    shortcuts = (ROOT / "tools/dev/refresh_owner_packlab_shortcuts.ps1").read_text(encoding="utf-8")
    post = (ROOT / "tools/dev/post_codex_owner_dev_refresh.ps1").read_text(encoding="utf-8")
    policy = (
        ROOT / "coordination/sessions/M16-C001/OWNER_DEV_POST_CODEX_REFRESH_POLICY_V01.md"
    ).read_text(encoding="utf-8")
    assert "uv sync --locked" in deploy
    assert "ls-tree -r --name-only $sha" in deploy
    assert "Copy-Item -LiteralPath $source -Destination $destination -Force" in deploy
    assert "reconstruction-work|reconstruction-output|packlab-work" in deploy
    assert "OWNER_DEV_RUNTIME_READY" in deploy and "releases" in deploy
    assert "Move-Item -LiteralPath $stage -Destination $current" not in deploy
    current_refresh = (ROOT / "tools/dev/update_owner_dev_current_runtime.ps1").read_text(
        encoding="utf-8"
    )
    post = (ROOT / "tools/dev/post_codex_owner_dev_refresh.ps1").read_text(encoding="utf-8")
    assert "Copy-Item -LiteralPath $_.FullName" in current_refresh
    assert post.index("refresh_owner_packlab_shortcuts.ps1") < post.index(
        "update_owner_dev_current_runtime.ps1"
    )
    assert "sourcePathsBase64" in deploy and "base64.b64decode" in deploy
    assert "owner_packlab_bootstrap.py" in launcher
    assert '"pythonw.exe"' in launcher
    assert 'run_module("packlab_studio"' in bootstrap
    assert "WaitForExit(200)" in launcher and "StartupStabilitySeconds = 10" in launcher
    assert "early_child_exit" in launcher and "MessageBox.Show" in launcher
    assert "powershell.exe" not in launcher.lower()
    assert "/target:winexe" in build and "/win32icon" in build
    assert "OWNER_DEV_LAUNCHER_BUILT" in build and "GUI_ICON_OK" in build
    assert "OWNER_DEV_LAUNCHER_REUSED" in build and "PackLab.build.json" in build
    assert "ExpectedSourceCommit" in launcher and "runtime_id" in launcher
    assert "OWNER_DEV_EXE_READY" in shortcuts
    assert "MoveFileEx" in shortcuts and "PackLab.lnk" in shortcuts
    assert "--no-install-project" in deploy
    assert "owner_packlab_bootstrap.py" in deploy
    post = (ROOT / "tools/dev/post_codex_owner_dev_refresh.ps1").read_text(encoding="utf-8")
    assert "rev-parse HEAD" in post and "runtimeFields" in post
    assert " OWNER_DEV_EXE_READY" in post or "OWNER_DEV_EXE_READY" in post
    assert "OWNER_DEV_READY" not in post
    assert "OWNER_DEV_EXE_READY" in policy
    assert "GUI-subsystem" in policy and "PackLab.exe" in policy
    assert "PACKLAB_OWNERDEV_DIAGNOSTICS" in launcher
    assert "a4a655fc92796413130633703602885671f5b1a0773d045ebc79d6bd522c7fc1" in build
    assert "SHChangeNotify" in shortcuts
    assert "Taskband" not in shortcuts and "Explorer" not in shortcuts


def test_runtime_manifest_contract_excludes_owner_local_paths() -> None:
    scripts = "\n".join(
        path.read_text(encoding="utf-8") for path in (ROOT / "tools/dev").glob("*.ps1")
    )
    assert "source_commit = $sha" in scripts
    assert "icon_sha256 = $iconHash" in scripts
    assert "smoke_status = 'PASS'" in scripts
    assert not re.search(r"C:\\Users\\[^\s\"']+", scripts, re.IGNORECASE)
    assert (
        json.loads((ROOT / "apps/windows-studio/assets/branding/icon_manifest.json").read_text())[
            "schema_version"
        ]
        == 1
    )


def test_native_launcher_build_and_runtime_failure_paths(tmp_path: Path) -> None:
    if not shutil.which("powershell.exe"):
        return
    csc = Path(os.environ["WINDIR"]) / "Microsoft.NET/Framework64/v4.0.30319/csc.exe"
    if not csc.is_file():
        csc = Path(os.environ["WINDIR"]) / "Microsoft.NET/Framework/v4.0.30319/csc.exe"
    assert csc.is_file(), "V09 requires an already-installed Windows C# compiler"
    owner_root = tmp_path / "owner runtime with spaces"
    runtime_id = "a" * 40 + "-" + "b" * 32
    release = owner_root / "releases" / runtime_id
    icon = release / "apps/windows-studio/assets/branding/PackLab.ico"
    icon.parent.mkdir(parents=True)
    icon.write_bytes((ROOT / "apps/windows-studio/assets/branding/PackLab.ico").read_bytes())
    lock_bytes = b"test locked dependencies\n"
    (release / "uv.lock").write_bytes(lock_bytes)
    lock_digest = hashlib.sha256(lock_bytes).hexdigest()
    build = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-File",
            str(ROOT / "tools/dev/build_owner_packlab_exe.ps1"),
            "-RepositoryRoot",
            str(ROOT),
            "-OwnerRoot",
            str(owner_root),
            "-SourceCommit",
            "a" * 40,
            "-RuntimeId",
            runtime_id,
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert build.returncode == 0, build.stdout + build.stderr
    assert "GUI_ICON_OK" in build.stdout
    launcher = owner_root / "launcher/PackLab.exe"
    assert launcher.is_file() and launcher.stat().st_size > 20_000
    first_launcher = launcher.read_bytes()
    repeated_build = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-File",
            str(ROOT / "tools/dev/build_owner_packlab_exe.ps1"),
            "-RepositoryRoot",
            str(ROOT),
            "-OwnerRoot",
            str(owner_root),
            "-SourceCommit",
            "a" * 40,
            "-RuntimeId",
            runtime_id,
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert repeated_build.returncode == 0, repeated_build.stdout + repeated_build.stderr
    assert "OWNER_DEV_LAUNCHER_REUSED" in repeated_build.stdout
    assert launcher.read_bytes() == first_launcher
    digest = hashlib.sha256(icon.read_bytes()).hexdigest()
    (release / "owner-dev-runtime.json").write_text(
        json.dumps(
            {
                "source_commit": "a" * 40,
                "runtime_id": runtime_id,
                "uv_lock_sha256": lock_digest,
                "studio_version": "0.1.0",
                "python_version": "Python 3.12.10",
                "smoke_status": "PASS",
                "icon_sha256": digest,
            }
        ),
        encoding="utf-8",
    )
    desktop = tmp_path / "Desktop with spaces"
    programs = tmp_path / "Start Menu with spaces"
    desktop.mkdir()
    obsolete = desktop / "PackLab.lnk"
    obsolete.write_bytes(b"obsolete owner shortcut")
    unrelated = desktop / "PackLab 3D.lnk"
    unrelated.write_bytes(b"unrelated shortcut")
    environment = os.environ.copy()
    environment["PACKLAB_OWNERDEV_DESKTOP_OVERRIDE"] = str(desktop)
    environment["PACKLAB_OWNERDEV_PROGRAMS_OVERRIDE"] = str(programs)
    deployed = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-File",
            str(ROOT / "tools/dev/refresh_owner_packlab_shortcuts.ps1"),
            "-OwnerRoot",
            str(owner_root),
            "-RuntimeId",
            runtime_id,
        ],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )
    assert deployed.returncode == 0, deployed.stdout + deployed.stderr
    desktop_exe = desktop / "PackLab.exe"
    assert desktop_exe.read_bytes() == launcher.read_bytes()
    assert not obsolete.exists()
    assert unrelated.read_bytes() == b"unrelated shortcut"
    assert "OWNER_DEV_EXE_READY " + "a" * 40 + " " + runtime_id in deployed.stdout
    assert (programs / "PackLab/PackLab.lnk").is_file()

    test_launcher = tmp_path / "launcher with spaces.exe"
    test_source = tmp_path / "PackLabOwnerLauncher.test.cs"
    test_source.write_text(
        (ROOT / "tools/dev/PackLabOwnerLauncher.cs")
        .read_text(encoding="utf-8")
        .replace("__PACKLAB_SOURCE_COMMIT__", "a" * 40)
        .replace("__PACKLAB_RUNTIME_ID__", runtime_id),
        encoding="utf-8",
    )
    compile_test = subprocess.run(
        [
            str(csc),
            "/nologo",
            "/target:winexe",
            "/define:OWNERDEV_TEST",
            f"/out:{test_launcher}",
            f"/win32icon:{ROOT / 'apps/windows-studio/assets/branding/PackLab.ico'}",
            "/reference:System.Windows.Forms.dll",
            str(test_source),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert compile_test.returncode == 0, compile_test.stdout + compile_test.stderr

    local_app_data = tmp_path / "la"
    result_file = tmp_path / "native error dialog result.txt"
    environment = os.environ.copy()
    environment["LOCALAPPDATA"] = str(local_app_data)
    environment["PACKLAB_OWNERDEV_TEST_RESULT"] = str(result_file)
    missing = subprocess.run([str(test_launcher)], env=environment, check=False, timeout=5)
    assert missing.returncode == 1
    assert "dialog_shown=true" in result_file.read_text(encoding="utf-8")
    logs = list((local_app_data / "PackLab/OwnerDev/logs").glob("startup-*.log"))
    assert logs and "reason=launcher_failure" in logs[0].read_text(encoding="utf-8")

    runtime_id = "a" * 40 + "-" + "b" * 32
    release_runtime = local_app_data / "PackLab/OwnerDev/releases" / runtime_id
    release_runtime.mkdir(parents=True, exist_ok=True)
    (release_runtime / "uv.lock").write_bytes(lock_bytes)
    pythonw = release_runtime / ".venv/Scripts/pythonw.exe"
    pythonw.parent.mkdir(parents=True)
    fake_child_source = tmp_path / "early_exit.cs"
    fake_child_source.write_text(
        "internal static class EarlyExit { private static int Main() { return 29; } }",
        encoding="utf-8",
    )
    fake_child = subprocess.run(
        [str(csc), "/nologo", "/target:winexe", f"/out:{pythonw}", str(fake_child_source)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert fake_child.returncode == 0, fake_child.stdout + fake_child.stderr
    # Test launcher constants are replaced in a temporary source copy below.
    (release_runtime / "owner-dev-runtime.json").write_text(
        json.dumps(
            {
                "source_commit": "a" * 40,
                "runtime_id": runtime_id,
                "uv_lock_sha256": lock_digest,
                "studio_version": "0.1.0",
                "smoke_status": "PASS",
            }
        ),
        encoding="utf-8",
    )
    result_file.unlink()
    missing_bootstrap = subprocess.run(
        [str(test_launcher)], env=environment, check=False, timeout=5
    )
    assert missing_bootstrap.returncode == 1
    assert "dialog_shown=true" in result_file.read_text(encoding="utf-8")
    assert "bootstrap script is missing" in "\n".join(
        path.read_text(encoding="utf-8")
        for path in (local_app_data / "PackLab/OwnerDev/logs").glob("startup-*.log")
    )

    bootstrap = release_runtime / "tools/dev/owner_packlab_bootstrap.py"
    bootstrap.parent.mkdir(parents=True)
    bootstrap.write_text("# fixture\n", encoding="utf-8")
    result_file.unlink()
    early = subprocess.run([str(test_launcher)], env=environment, check=False, timeout=15)
    assert early.returncode == 1
    diagnostic = result_file.read_text(encoding="utf-8")
    assert "dialog_shown=true" in diagnostic and "exit_code=29" in diagnostic
    logs = list((local_app_data / "PackLab/OwnerDev/logs").glob("startup-*.log"))
    assert any("reason=early_child_exit" in path.read_text(encoding="utf-8") for path in logs)


def test_failed_locked_sync_preserves_previous_runtime(tmp_path: Path) -> None:
    repository = tmp_path / "clean repo with spaces"
    repository.mkdir()
    for relative in (
        "pyproject.toml",
        "uv.lock",
        "core/src",
        "apps/windows-studio/src",
        "apps/windows-studio/assets/branding",
        "schemas",
        "assets",
        "tools/dev/launch_owner_packlab.ps1",
    ):
        path = repository / relative
        if "." in path.name and not path.suffix == "":
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("fixture\n")
        else:
            path.mkdir(parents=True, exist_ok=True)
    for command in (
        ["git", "init", "-q", str(repository)],
        ["git", "-C", str(repository), "config", "user.email", "ownerdev-test@example.invalid"],
        ["git", "-C", str(repository), "config", "user.name", "Owner Dev Test"],
        ["git", "-C", str(repository), "add", "-A"],
        ["git", "-C", str(repository), "commit", "-qm", "fixture"],
    ):
        subprocess.run(command, check=True, capture_output=True, text=True)

    local_app_data = tmp_path / "Local AppData"
    existing_release = local_app_data / "PackLab/OwnerDev/releases" / ("a" * 40 + "-" + "c" * 32)
    existing_release.mkdir(parents=True)
    sentinel = existing_release / "known-good.txt"
    sentinel.write_text("previous runtime stays intact")
    fake_uv = tmp_path / "uv fails.cmd"
    fake_uv.write_text("@echo off\r\nexit /b 97\r\n")
    environment = os.environ.copy()
    environment["LOCALAPPDATA"] = str(local_app_data)
    result = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-File",
            str(ROOT / "tools/dev/update_owner_dev_runtime.ps1"),
            "-RepositoryRoot",
            str(repository),
            "-UvPath",
            str(fake_uv),
        ],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )
    assert result.returncode != 0
    assert sentinel.read_text() == "previous runtime stays intact"
    assert list((local_app_data / "PackLab/OwnerDev/releases").glob("a" * 40 + "-*")) == [
        existing_release
    ]


def test_compatibility_current_runtime_switch_preserves_releases(tmp_path: Path) -> None:
    if not shutil.which("powershell.exe"):
        return
    owner_root = tmp_path / "owner runtime with spaces"
    first_id = "a" * 40 + "-" + "b" * 32
    second_id = "c" * 40 + "-" + "d" * 32
    first_release = owner_root / "releases" / first_id
    second_release = owner_root / "releases" / second_id
    first_release.mkdir(parents=True)
    second_release.mkdir(parents=True)
    lock_bytes = b"immutable dependency lock\n"
    for release, runtime_id, source_sha in (
        (first_release, first_id, "a" * 40),
        (second_release, second_id, "c" * 40),
    ):
        (release / "uv.lock").write_bytes(lock_bytes)
        (release / "owner-dev-runtime.json").write_text(
            json.dumps(
                {
                    "runtime_id": runtime_id,
                    "source_commit": source_sha,
                    "uv_lock_sha256": hashlib.sha256(lock_bytes).hexdigest(),
                    "smoke_status": "PASS",
                }
            ),
            encoding="utf-8",
        )
    current = owner_root / "current"
    current.mkdir(parents=True)
    (current / "preserved.txt").write_text("keep prior owner runtime")

    def switch(runtime_id: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-File",
                str(ROOT / "tools/dev/update_owner_dev_current_runtime.ps1"),
                "-OwnerRoot",
                str(owner_root),
                "-RuntimeId",
                runtime_id,
            ],
            check=False,
            capture_output=True,
            text=True,
        )

    first = switch(first_id)
    assert first.returncode == 0, first.stdout + first.stderr
    assert current.is_dir() and not current.is_symlink()
    assert json.loads((current / "owner-dev-runtime.json").read_text())["runtime_id"] == first_id
    preserved = list(owner_root.glob("previous-*"))
    assert (
        len(preserved) == 1
        and (preserved[0] / "preserved.txt").read_text() == "keep prior owner runtime"
    )

    second = switch(second_id)
    assert second.returncode == 0, second.stdout + second.stderr
    assert current.is_dir() and not current.is_symlink()
    assert json.loads((current / "owner-dev-runtime.json").read_text())["runtime_id"] == second_id
    assert (first_release / "owner-dev-runtime.json").is_file()
