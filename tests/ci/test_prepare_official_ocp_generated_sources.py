from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path, PurePosixPath

import pytest
from tools.packaging.prepare_official_ocp_generated_sources import (
    ARCHIVE_ROOT,
    REMOVED_MODULES,
    _assert_non_vtk_sources_preserved,
    _assert_registration_inventory,
    _module_ids,
    _patch_source_files,
    _safe_members,
    prepare_generated_sources,
)


def _registration_source(modules: set[str]) -> str:
    lines = [f"void register_{module}_enums(py::module&);" for module in sorted(modules)]
    lines.extend(f"void register_{module}(py::module&);" for module in sorted(modules))
    lines.extend(f"register_{module}_enums(m);" for module in sorted(modules))
    lines.extend(f"register_{module}(m);" for module in sorted(modules))
    return "\n".join(lines) + "\n"


def _source_names(modules: set[str]) -> set[str]:
    return {
        f"{ARCHIVE_ROOT}/{module}{suffix}"
        for module in modules
        for suffix in (".cpp", "_pre.cpp", "_tmpl.hxx")
    }


def _cmake() -> str:
    return """find_package( fmt REQUIRED )
find_package( pybind11 REQUIRED )
find_package( VTK REQUIRED
  COMPONENTS
    WrappingPythonCore
    RenderingCore
    RenderingOpenGL2
    CommonDataModel
    CommonExecutionModel
    freetype
)
message(STATUS "VTK ${VTK_VERSION} found")
find_package( OpenCASCADE REQUIRED )
target_link_libraries( OCP PRIVATE ${OpenCASCADE_LIBRARIES} )
target_link_libraries( OCP PRIVATE pybind11::pybind11 VTK::WrappingPythonCore VTK::RenderingCore VTK::CommonDataModel VTK::CommonExecutionModel fmt::fmt)
"""


def test_source_inventory_rejects_missing_extra_and_duplicate_module_ids() -> None:
    modules = {"BRep", "gp"}
    _assert_registration_inventory(_registration_source(modules), modules)
    with pytest.raises(ValueError, match="exactly match"):
        _assert_registration_inventory(_registration_source(modules - {"gp"}), modules)

    extra_names = _source_names(modules | {"Extra"})
    assert _module_ids(extra_names) == modules | {"Extra"}
    with pytest.raises(ValueError, match="incomplete"):
        _module_ids(_source_names(modules) - {f"{ARCHIVE_ROOT}/gp_tmpl.hxx"})

    duplicate_case_name = _source_names(modules) | {f"{ARCHIVE_ROOT}/brep.cpp"}
    with pytest.raises(ValueError, match="case-colliding"):
        _module_ids(duplicate_case_name)


def test_patch_rewrites_real_fixture_files_and_removes_only_four_vtk_modules(
    tmp_path: Path,
) -> None:
    modules = set(REMOVED_MODULES) | {"BRep"}
    source_root = tmp_path / ARCHIVE_ROOT
    for name in _source_names(modules):
        relative = Path(*PurePosixPath(name).relative_to(ARCHIVE_ROOT).parts)
        source_root.mkdir(parents=True, exist_ok=True)
        (source_root / relative).write_text(f"source {relative.name}\n", encoding="utf-8")
    (source_root / "OCP.cpp").write_text(_registration_source(modules), encoding="utf-8")
    (source_root / "CMakeLists.txt").write_text(_cmake(), encoding="utf-8")
    original_files = {
        path.name: path.read_bytes() for path in source_root.iterdir() if path.is_file()
    }
    patched_cpp, patched_cmake, retained = _patch_source_files(
        source_root, modules, _registration_source(modules), _cmake()
    )
    preserved = [
        {
            "relative_path": f"{ARCHIVE_ROOT}/{name}",
            "byte_length": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        }
        for name, data in original_files.items()
    ]
    patched_records = [
        {
            "relative_path": f"{ARCHIVE_ROOT}/{path.name}",
            "byte_length": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
        for path in source_root.iterdir()
        if path.is_file()
    ]

    assert retained == {"BRep"}
    assert _module_ids({f"{ARCHIVE_ROOT}/{path.name}" for path in source_root.iterdir()}) == {
        "BRep"
    }
    assert "register_IVtk" not in patched_cpp
    assert "register_BRep" in patched_cpp
    assert "VTK" not in patched_cmake.upper()
    assert "pybind11::pybind11 fmt::fmt" in patched_cmake
    assert (source_root / "BRep.cpp").is_file()
    assert not (source_root / "IVtk.cpp").exists()
    _assert_non_vtk_sources_preserved(preserved, patched_records)


def test_archive_rejects_traversal_and_case_colliding_paths(tmp_path: Path) -> None:
    traversal = tmp_path / "traversal.zip"
    with zipfile.ZipFile(traversal, "w") as archive:
        archive.writestr("../escape.txt", "unsafe")
    with zipfile.ZipFile(traversal) as archive, pytest.raises(ValueError, match="unsafe ZIP"):
        _safe_members(archive)

    drive_path = tmp_path / "drive-path.zip"
    with zipfile.ZipFile(drive_path, "w") as archive:
        archive.writestr("C:/escape.txt", "unsafe")
    with zipfile.ZipFile(drive_path) as archive, pytest.raises(ValueError, match="unsafe ZIP"):
        _safe_members(archive)

    dot_segment = tmp_path / "dot-segment.zip"
    with zipfile.ZipFile(dot_segment, "w") as archive:
        archive.writestr(f"{ARCHIVE_ROOT}/./escape.pyi", "unsafe")
    with zipfile.ZipFile(dot_segment) as archive, pytest.raises(ValueError, match="unsafe ZIP"):
        _safe_members(archive)

    nested = tmp_path / "nested-stub.zip"
    with zipfile.ZipFile(nested, "w") as archive:
        archive.writestr(f"{ARCHIVE_ROOT}/OCP-stubs/__init__.pyi", "safe")
    with zipfile.ZipFile(nested) as archive:
        assert len(_safe_members(archive)) == 1

    collision = tmp_path / "collision.zip"
    with zipfile.ZipFile(collision, "w") as archive:
        archive.writestr(f"{ARCHIVE_ROOT}/File.cpp", "one")
        archive.writestr(f"{ARCHIVE_ROOT}/file.cpp", "two")
    with zipfile.ZipFile(collision) as archive, pytest.raises(ValueError, match="case-colliding"):
        _safe_members(archive)


def test_wrong_archive_hash_fails_before_extraction(tmp_path: Path) -> None:
    archive = tmp_path / "wrong.zip"
    archive.write_bytes(b"not the locked official archive")
    destination = tmp_path / "output"
    with pytest.raises(ValueError, match="size or SHA-256"):
        prepare_generated_sources(archive, destination, tmp_path / "manifest.json")
    assert not destination.exists()
