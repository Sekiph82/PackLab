from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

from packlab_studio import branding
from packlab_studio.app import create_application
from packlab_studio.shell import StudioMainWindow

ROOT = Path(__file__).resolve().parents[2]
ICON = ROOT / "apps/windows-studio/assets/branding/PackLab.ico"


def test_canonical_icon_and_brand_manifest_match() -> None:
    digest = hashlib.sha256(ICON.read_bytes()).hexdigest()
    manifest = json.loads((ICON.parent / "icon_manifest.json").read_text(encoding="utf-8"))
    asset = manifest["assets"][0]
    assert asset["path"] == "apps/windows-studio/assets/branding/PackLab.ico"
    assert asset["source_sha256"] == digest
    assert asset["copied_sha256"] == digest


def test_icon_helper_falls_back_without_crashing(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(branding, "packlab_data_root", lambda: tmp_path)
    assert branding.application_icon().isNull()


def test_application_and_window_use_canonical_icon(monkeypatch) -> None:
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app = create_application(["packlab-ownerdev-test"])
    window = StudioMainWindow()
    assert branding.icon_path() == ICON
    assert not app.windowIcon().isNull()
    assert not window.windowIcon().isNull()
    window.close()
    app.processEvents()


def test_app_user_model_id_is_guarded_on_non_windows(monkeypatch) -> None:
    monkeypatch.setattr(branding.os, "name", "posix")
    assert branding.set_windows_app_user_model_id() is False


def test_app_user_model_id_uses_explicit_windows_identity(monkeypatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr(branding.os, "name", "nt")
    monkeypatch.setattr(
        branding.ctypes,
        "windll",
        SimpleNamespace(
            shell32=SimpleNamespace(
                SetCurrentProcessExplicitAppUserModelID=lambda value: calls.append(value) or 0
            )
        ),
        raising=False,
    )
    assert branding.set_windows_app_user_model_id() is True
    assert calls == ["PackLab.Studio"]
