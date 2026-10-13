from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from tools.packaging.build_controlled_ocp_from_generated_sources import (
    _package_init_source,
    _path_free_dependency_audit,
)
from tools.packaging.validate_controlled_ocp_manifest import (
    load_and_validate_manifest,
    validate_staged_tree,
)
from tools.packaging.windows_sdk_source_lock_compatibility import (
    validate_sdk_source_lock_compatibility,
    validate_sdk_toolchain_contract_compatibility,
)

ROOT = Path(__file__).resolve().parents[2]
SOURCE_LOCK = ROOT / "tools" / "packaging" / "windows_native_source_lock.json"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def test_monolithic_extension_package_init_aliases_exact_retained_modules() -> None:
    modules = [f"Module{index:03}" for index in range(315)]
    modules[0] = "BRepCheck"
    source = _package_init_source(modules)

    assert "'BRepCheck'" in source
    assert "'Module314'" in source
    assert "sys.modules[f'{__name__}.{_module_name}'] = _module" in source
    assert "IVtk" not in source
    assert source == _package_init_source(modules)

    with pytest.raises(ValueError, match="315 unique module names"):
        _package_init_source(["BRepCheck"])
    duplicated = list(modules)
    duplicated[1] = "BRepCheck"
    with pytest.raises(ValueError, match="315 unique module names"):
        _package_init_source(duplicated)


def test_dependency_audit_manifest_projection_omits_host_paths_and_logs() -> None:
    result = _path_free_dependency_audit(
        {
            "status": "PASS",
            "windows_opengl_system": {
                "windows_sdk_root": r"C:\Program Files\Windows Kits\10",
                "gl_header": r"C:\Program Files\Windows Kits\10\Include\gl.h",
                "windows_sdk_version": "10.0.26100.0",
                "gl_header_present": True,
                "opengl32_import_library_present": True,
                "opengl32_system_runtime_present": True,
            },
            "opengl_compile_link_probe": {
                "status": "PASS",
                "header": "OpenGl_Context.hxx",
                "link_closure": "OpenCASCADE_LIBRARIES + opengl32",
                "executable_bytes": 4096,
                "log_tail": r"D:\a\PackLab\generated\build output",
            },
        }
    )
    serialized = json.dumps(result)
    assert "C:\\\\Program Files" not in serialized
    assert "D:\\\\a" not in serialized
    assert "log_tail" not in serialized
    assert result["windows_opengl_system"]["windows_sdk_version"] == "10.0.26100.0"


@pytest.fixture
def controlled_manifest(tmp_path: Path) -> tuple[Path, dict[str, object], dict[str, bytes]]:
    source_lock = json.loads(SOURCE_LOCK.read_text(encoding="utf-8"))
    records = {row["id"]: row for row in source_lock["records"]}
    files = {
        "OCP/OCP.cp312-win_amd64.pyd": b"binding",
        "OCP/TKBRep.dll": b"occt-runtime",
        "OCP/fmt.dll": b"fmt-runtime",
    }
    manifest = {
        "schema_version": 1,
        "status": "PASS",
        "input_lock_sha256": digest(SOURCE_LOCK.read_bytes()),
        "occt_sdk_checkpoint": {
            "source_lock_sha256": digest(SOURCE_LOCK.read_bytes()),
            "source_lock_compatibility": validate_sdk_source_lock_compatibility(
                {"source_lock_sha256": digest(SOURCE_LOCK.read_bytes())}, SOURCE_LOCK
            ),
            "toolchain_contract_sha256": digest(
                (ROOT / "tools" / "packaging" / "controlled_ocp_runtime_contract.json").read_bytes()
            ),
            "toolchain_contract_compatibility": validate_sdk_toolchain_contract_compatibility(
                {
                    "toolchain_contract_sha256": digest(
                        (
                            ROOT / "tools" / "packaging" / "controlled_ocp_runtime_contract.json"
                        ).read_bytes()
                    )
                }
            ),
        },
        "windows_runtime_deployment": json.loads(
            (ROOT / "tools" / "packaging" / "controlled_ocp_runtime_contract.json").read_text(
                encoding="utf-8"
            )
        )["windows_runtime_deployment"],
        "native_import_ownership": {
            "fmt": {
                "source_package_id": "fmt-source-12.1.0",
                "deployment_role": "APP_SHIPPED_THIRD_PARTY",
                "binary_package": records["fmt-source-12.1.0"]["binary_package"],
                "binary_sha256": "0d4edfe1411f4a7c5f57758239f0f1e6e1cff7f2d0ae5f9511a1dfacc08b388d",
                "source_revision": records["fmt-source-12.1.0"]["revision"],
                "license_identifier": records["fmt-source-12.1.0"]["license_identifier"],
                "license_notice_source": records["fmt-source-12.1.0"]["license_notice_source"],
                "license_notice_sha256": records["fmt-source-12.1.0"]["license_notice_sha256"],
                "recipe": records["fmt-source-12.1.0"]["recipe"],
            },
            "windows_os_and_vc_prerequisite_imports": ["api-ms-win-crt-runtime-l1-1-0.dll"],
            "resolved_external_imports": [
                {
                    "name": "api-ms-win-crt-runtime-l1-1-0.dll",
                    "deployment_role": "WINDOWS_OS_COMPONENT",
                    "resolved_host": "ucrtbase.dll",
                    "host_sha256": "a" * 64,
                }
            ],
        },
        "windows_runtime_policy_evidence": {
            "status": "PASS",
            "prerequisite_policy_sha256": digest(
                (ROOT / "tools/packaging/windows-runtime-prerequisite.json").read_bytes()
            ),
            "vc_runtime": {"deployment_role": "MICROSOFT_SIGNED_PREREQUISITE"},
            "negative_prerequisite_simulations": {
                "missing": False,
                "wrong_architecture": False,
                "below_minimum": False,
            },
        },
        "files": [],
    }
    for relative, content in files.items():
        source_id = (
            "ocp-source-7.9.3.1.1"
            if relative.endswith(".pyd")
            else "fmt-source-12.1.0"
            if relative.endswith("fmt.dll")
            else "occt-source-7.9.3"
        )
        record = records[source_id]
        manifest["files"].append(
            {
                "relative_path": relative,
                "sha256": digest(content),
                "owning_component": record["component"],
                "source_package_id": source_id,
                "version": record["version"],
                "build_revision": record["revision"],
                "license_identifier": record["license_identifier"],
                "license_notice_source": record["license_notice_source"],
                "production_purpose": "test fixture",
                "deployment_role": (
                    "OCP_SOURCE_BUILT"
                    if source_id == "ocp-source-7.9.3.1.1"
                    else "APP_SHIPPED_THIRD_PARTY"
                    if source_id == "fmt-source-12.1.0"
                    else "OCCT_OWNED"
                ),
                **(
                    {
                        "binary_sha256": "0d4edfe1411f4a7c5f57758239f0f1e6e1cff7f2d0ae5f9511a1dfacc08b388d",
                        "binary_byte_length": 187511,
                        "binary_package": record["binary_package"],
                        "recipe": record["recipe"],
                    }
                    if source_id == "fmt-source-12.1.0"
                    else {}
                ),
            }
        )
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return manifest_path, manifest, files


def test_controlled_ocp_manifest_binds_exact_lock_and_stage(
    tmp_path: Path, controlled_manifest: tuple[Path, dict[str, object], dict[str, bytes]]
) -> None:
    manifest_path, _, files = controlled_manifest
    manifest = load_and_validate_manifest(manifest_path, SOURCE_LOCK)
    stage = tmp_path / "PackLabStudio"
    for relative, content in files.items():
        destination = stage / "_internal" / Path(relative)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
    validate_staged_tree(stage, manifest)


def test_controlled_ocp_manifest_rejects_unmanifested_extension(
    tmp_path: Path, controlled_manifest: tuple[Path, dict[str, object], dict[str, bytes]]
) -> None:
    manifest_path, _, files = controlled_manifest
    manifest = load_and_validate_manifest(manifest_path, SOURCE_LOCK)
    stage = tmp_path / "PackLabStudio"
    for relative, content in files.items():
        destination = stage / "_internal" / Path(relative)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
    (stage / "_internal" / "OCP" / "Opaque.pyd").write_bytes(b"unmapped")
    with pytest.raises(ValueError, match="without controlled provenance"):
        validate_staged_tree(stage, manifest)


def test_controlled_ocp_manifest_rejects_missing_native_file(
    tmp_path: Path, controlled_manifest: tuple[Path, dict[str, object], dict[str, bytes]]
) -> None:
    manifest_path, _, files = controlled_manifest
    manifest = load_and_validate_manifest(manifest_path, SOURCE_LOCK)
    stage = tmp_path / "PackLabStudio"
    relative, content = next(iter(files.items()))
    destination = stage / "_internal" / Path(relative)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(content)
    with pytest.raises(ValueError, match="manifest and staged native files differ"):
        validate_staged_tree(stage, manifest)


def test_controlled_ocp_stage_rejects_windows_runtime_copy(
    tmp_path: Path, controlled_manifest: tuple[Path, dict[str, object], dict[str, bytes]]
) -> None:
    manifest_path, _, files = controlled_manifest
    manifest = load_and_validate_manifest(manifest_path, SOURCE_LOCK)
    stage = tmp_path / "PackLabStudio"
    for relative, content in files.items():
        destination = stage / "_internal" / Path(relative)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
    (stage / "_internal" / "PySide6" / "vcruntime140.dll").parent.mkdir(parents=True)
    (stage / "_internal" / "PySide6" / "vcruntime140.dll").write_bytes(b"runtime copy")
    with pytest.raises(ValueError, match="Windows OS or VC prerequisite runtime DLL"):
        validate_staged_tree(stage, manifest)


def test_fmt_manifest_record_requires_exact_package_and_binary_identity(
    tmp_path: Path, controlled_manifest: tuple[Path, dict[str, object], dict[str, bytes]]
) -> None:
    manifest_path, manifest, _ = controlled_manifest
    lock = json.loads(SOURCE_LOCK.read_text(encoding="utf-8"))
    record = next(item for item in lock["records"] if item["id"] == "fmt-source-12.1.0")
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    assert len(load_and_validate_manifest(manifest_path, SOURCE_LOCK)["files"]) == 3
    fmt_entry = next(
        item for item in manifest["files"] if item["source_package_id"] == record["id"]
    )
    fmt_entry["binary_package"]["sha256"] = "0" * 64
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="fmt.dll is not bound"):
        load_and_validate_manifest(manifest_path, SOURCE_LOCK)
