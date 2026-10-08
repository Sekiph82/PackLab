from __future__ import annotations

import sys

from packlab_studio import frozen_runtime


def test_register_frozen_native_directories_keeps_handles_and_skips_missing_dirs(
    monkeypatch, tmp_path
) -> None:
    (tmp_path / "PySide6").mkdir()
    (tmp_path / "shiboken6").mkdir()
    (tmp_path / "OCP").mkdir()
    registered: list[str] = []
    handles: list[object] = []

    def add_directory(path: str) -> object:
        registered.append(path)
        handle = object()
        handles.append(handle)
        return handle

    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    monkeypatch.setattr(frozen_runtime.os, "add_dll_directory", add_directory)
    frozen_runtime._DLL_DIRECTORY_HANDLES.clear()

    result = frozen_runtime.register_frozen_native_directories()

    assert result == ("PySide6", "shiboken6", "OCP")
    assert registered == [
        str(tmp_path / "PySide6"),
        str(tmp_path / "shiboken6"),
        str(tmp_path / "OCP"),
    ]
    assert frozen_runtime._DLL_DIRECTORY_HANDLES == handles


def test_register_frozen_native_directories_is_noop_outside_frozen_windows(monkeypatch) -> None:
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setattr(sys, "frozen", True, raising=False)

    assert frozen_runtime.register_frozen_native_directories() == ()
