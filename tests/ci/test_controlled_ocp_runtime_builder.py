from __future__ import annotations

from pathlib import Path

import pytest
from tools.packaging.build_controlled_ocp_runtime import find_generated_binding


def test_generated_binding_comes_from_the_separate_native_build(tmp_path: Path) -> None:
    generated = tmp_path / "ocp-build" / "OCP"
    generated.mkdir(parents=True)
    (generated / "OCP.cpp").write_text("// generated binding source\n", encoding="utf-8")
    native = tmp_path / "native-build" / "Release"
    native.mkdir(parents=True)
    extension = native / "OCP.cp312-win_amd64.pyd"
    extension.write_bytes(b"native binding fixture")

    package, binding = find_generated_binding(tmp_path / "ocp-build", tmp_path / "native-build")

    assert package == generated
    assert binding == extension


def test_generated_binding_rejects_missing_cpp_sources(tmp_path: Path) -> None:
    (tmp_path / "ocp-build" / "OCP").mkdir(parents=True)

    with pytest.raises(ValueError, match=r"generated OCP C\+\+ sources"):
        find_generated_binding(tmp_path / "ocp-build", tmp_path / "native-build")


def test_builder_configures_and_compiles_pywrap_generated_cmake_project() -> None:
    builder = (
        Path(__file__).resolve().parents[2] / "tools/packaging/build_controlled_ocp_runtime.py"
    ).read_text(encoding="utf-8")

    assert 'generated_cmake = ocp_build / "OCP" / "CMakeLists.txt"' in builder
    assert '"-S",\n            str(generated_cmake.parent)' in builder
    assert 'native_build = args.build_root / "ocp-native-build"' in builder
    assert '"--target",\n            "OCP"' in builder
    assert "find_generated_binding(ocp_build, native_build)" in builder


def test_generated_binding_rejects_missing_or_ambiguous_native_outputs(tmp_path: Path) -> None:
    generated = tmp_path / "ocp-build" / "OCP"
    generated.mkdir(parents=True)
    (generated / "OCP.cpp").write_text("// generated binding source\n", encoding="utf-8")
    release = tmp_path / "native-build" / "Release"
    release.mkdir(parents=True)

    with pytest.raises(ValueError, match="one unambiguous Python binding"):
        find_generated_binding(tmp_path / "ocp-build", tmp_path / "native-build")

    (release / "OCP.cp312-win_amd64.pyd").write_bytes(b"first")
    (release / "OCP.extra.cp312-win_amd64.pyd").write_bytes(b"second")
    with pytest.raises(ValueError, match="one unambiguous Python binding"):
        find_generated_binding(tmp_path / "ocp-build", tmp_path / "native-build")
