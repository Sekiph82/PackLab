from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_production_spec_embeds_branding_asset_and_executable_icon() -> None:
    spec = (ROOT / "tools/packaging/packlab_studio.spec").read_text(encoding="utf-8")
    assert "icon=str(icon_path)" in spec
    assert 'str(branding_path), "apps/windows-studio/assets/branding"' in spec


def test_owner_scripts_use_stable_runtime_and_atomic_staging() -> None:
    deploy = (ROOT / "tools/dev/update_owner_dev_runtime.ps1").read_text(encoding="utf-8")
    launch = (ROOT / "tools/dev/launch_owner_packlab.ps1").read_text(encoding="utf-8")
    shortcuts = (ROOT / "tools/dev/refresh_owner_packlab_shortcuts.ps1").read_text(encoding="utf-8")
    post = (ROOT / "tools/dev/post_codex_owner_dev_refresh.ps1").read_text(encoding="utf-8")
    assert "uv sync --locked" in deploy
    assert "Move-Item -LiteralPath $stage -Destination $current" in deploy
    assert "-m', 'packlab_studio'" in launch
    assert "GetFolderPath('DesktopDirectory')" in shortcuts
    assert "GetFolderPath('Programs')" in shortcuts
    assert "OWNER_DEV_READY" in post
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


def test_shortcut_refresh_supports_temp_known_folders_with_spaces(tmp_path: Path) -> None:
    owner_root = tmp_path / "owner runtime with spaces"
    current = owner_root / "current"
    (current / "tools/dev").mkdir(parents=True)
    icon = current / "apps/windows-studio/assets/branding/PackLab.ico"
    icon.parent.mkdir(parents=True)
    icon.write_bytes((ROOT / "apps/windows-studio/assets/branding/PackLab.ico").read_bytes())
    (current / "tools/dev/launch_owner_packlab.ps1").write_text("# shortcut target\n")
    digest = hashlib.sha256(icon.read_bytes()).hexdigest()
    (current / "owner-dev-runtime.json").write_text(
        json.dumps({"source_commit": "a" * 40, "smoke_status": "PASS", "icon_sha256": digest})
    )
    desktop = tmp_path / "Desktop with spaces"
    programs = tmp_path / "Start Menu with spaces"
    environment = os.environ.copy()
    environment["PACKLAB_OWNERDEV_DESKTOP_OVERRIDE"] = str(desktop)
    environment["PACKLAB_OWNERDEV_PROGRAMS_OVERRIDE"] = str(programs)
    result = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-File",
            str(ROOT / "tools/dev/refresh_owner_packlab_shortcuts.ps1"),
            "-OwnerRoot",
            str(owner_root),
        ],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert (desktop / "PackLab.lnk").is_file()
    assert (programs / "PackLab/PackLab.lnk").is_file()
    assert f"OWNER_DEV_SHORTCUTS_REFRESHED {'a' * 40}" in result.stdout


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
    current = local_app_data / "PackLab/OwnerDev/current"
    current.mkdir(parents=True)
    sentinel = current / "known-good.txt"
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
    assert not list((local_app_data / "PackLab/OwnerDev").glob("stage-*"))
