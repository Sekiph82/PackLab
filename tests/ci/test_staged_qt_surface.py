from __future__ import annotations

import json
from pathlib import Path

import pytest
from tools.packaging.assert_staged_qt_surface import inspect_stage

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "tools" / "packaging" / "qt_module_contract.json"


def _stage(tmp_path: Path, files: tuple[str, ...]) -> Path:
    stage = tmp_path / "stage"
    for relative in files:
        target = stage / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"fixture")
    return stage


def test_staged_qt_surface_accepts_only_contract_modules_and_plugins(tmp_path: Path) -> None:
    stage = _stage(
        tmp_path,
        (
            "PySide6/QtCore.pyd",
            "PySide6/QtGui.pyd",
            "PySide6/QtWidgets.pyd",
            "PySide6/QtSvg.pyd",
            "PySide6/QtPdf.pyd",
            "PySide6/QtNetwork.pyd",
            "PySide6/Qt6Core.dll",
            "PySide6/Qt6Gui.dll",
            "PySide6/Qt6Widgets.dll",
            "PySide6/Qt6Svg.dll",
            "PySide6/Qt6Pdf.dll",
            "PySide6/Qt6Network.dll",
            "PySide6/plugins/platforms/qwindows.dll",
            "PySide6/plugins/platforms/qoffscreen.dll",
        ),
    )

    report = inspect_stage(stage, CONTRACT)

    assert report["status"] == "PASS"
    assert report["unrelated_icu_runtime_dlls_absent"] is True
    assert "PySide6.QtPdf" in report["approved_staged_modules"]
    assert report["approved_staged_plugins"] == [
        "platforms/qoffscreen.dll",
        "platforms/qwindows.dll",
    ]


@pytest.mark.parametrize(
    "relative_path",
    (
        "PySide6/QtQml.pyd",
        "PySide6/QtVirtualKeyboard.pyd",
        "PySide6/plugins/platforminputcontexts/qtvirtualkeyboardplugin.dll",
        "PySide6/plugins/imageformats/qbmp.dll",
        "PySide6/Qt6Multimedia.dll",
        "icuuc.dll",
        "icudt78.dll",
        "open3d/examples/demo.ipynb",
        "open3d/nbextension/static.js",
    ),
)
def test_staged_qt_surface_rejects_unapproved_files(tmp_path: Path, relative_path: str) -> None:
    required = (
        "PySide6/QtCore.pyd",
        "PySide6/QtGui.pyd",
        "PySide6/QtWidgets.pyd",
        "PySide6/QtSvg.pyd",
        "PySide6/QtPdf.pyd",
    )
    stage = _stage(tmp_path, (*required, relative_path))

    with pytest.raises(ValueError):
        inspect_stage(stage, CONTRACT)


def test_qt_module_contract_is_json_and_requires_transitive_reason() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))

    assert contract["transitive_modules"]["PySide6.QtNetwork"]
    assert set(contract["direct_modules"]) == {
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtWidgets",
        "PySide6.QtSvg",
        "PySide6.QtPdf",
    }


def test_staged_qt_evidence_is_bound_to_the_exact_build(tmp_path: Path) -> None:
    stage = _stage(
        tmp_path,
        (
            "PySide6/QtCore.pyd",
            "PySide6/QtGui.pyd",
            "PySide6/QtWidgets.pyd",
            "PySide6/QtSvg.pyd",
            "PySide6/QtPdf.pyd",
        ),
    )
    report = inspect_stage(
        stage,
        CONTRACT,
        "a" * 40,
        "1.2.3",
    )

    assert report["PACKLAB_BUILD_REVISION"] == "a" * 40
    assert report["studio_version"] == "1.2.3"
