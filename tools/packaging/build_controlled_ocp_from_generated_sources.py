"""Compile the locked 315-module OCP binding from its official generated source ZIP."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from tools.packaging.audit_controlled_occt_sdk_dependencies import audit_dependencies
from tools.packaging.build_controlled_ocp_runtime import (
    is_external_runtime,
    pe_imports,
    sha256,
    windows_sdk_gl_include_dir,
)
from tools.packaging.prepare_official_ocp_generated_sources import prepare_generated_sources
from tools.packaging.validate_controlled_occt_sdk import validate_sdk
from tools.packaging.validate_windows_native_runtime_policy import (
    resolve_windows_api_set_host,
    validate_runtime,
)
from tools.packaging.validate_windows_native_source_lock import load_source_lock
from tools.packaging.windows_native_runtime_policy import is_windows_runtime_dll
from tools.packaging.windows_sdk_source_lock_compatibility import (
    validate_sdk_source_lock_compatibility,
    validate_sdk_toolchain_contract_compatibility,
)

LOCK = Path("tools/packaging/windows_native_source_lock.json")
CONTRACT = Path("tools/packaging/controlled_ocp_runtime_contract.json")
RUNTIME_POLICY = Path("tools/packaging/windows-runtime-prerequisite.json")
PARALLELISM = 4
GENERATOR = "Visual Studio 17 2022"
SDK_VERSION = "10.0.26100.0"
OCP_ID = "ocp-source-7.9.3.1.1"
OCCT_ID = "occt-source-7.9.3"
MAX_COMPILE_SECONDS = 270 * 60
REQUIRED_PACKLAB_MODULES = frozenset(
    {
        "BRep",
        "BRepAdaptor",
        "BRepAlgoAPI",
        "BRepBndLib",
        "BRepBuilderAPI",
        "BRepCheck",
        "BRepClass",
        "BRepLProp",
        "BRepMesh",
        "BRepOffsetAPI",
        "BRepPrimAPI",
        "BRepTools",
        "Bnd",
        "GeomAbs",
        "HLRAlgo",
        "HLRBRep",
        "IFSelect",
        "Interface",
        "STEPControl",
        "StlAPI",
        "TColStd",
        "TopAbs",
        "TopExp",
        "TopLoc",
        "TopTools",
        "TopoDS",
        "gp",
    }
)


def _run(command: list[str], *, timeout: int | None = None) -> None:
    print("RUN " + " ".join(command), flush=True)
    try:
        subprocess.run(command, check=True, timeout=timeout)
    except subprocess.TimeoutExpired as error:
        raise TimeoutError(
            f"controlled OCP phase exceeded its {timeout}-second safety budget"
        ) from error


def _compiler_version(sdk_manifest_path: Path) -> str:
    sdk = json.loads(sdk_manifest_path.read_text(encoding="utf-8"))
    return str(sdk["compiler"])


def build_from_generated_sources(args: argparse.Namespace) -> dict[str, Any]:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    runtime_policy = json.loads(RUNTIME_POLICY.read_text(encoding="utf-8"))
    runtime_contract = contract.get("windows_runtime_deployment", {})
    required_roles = {
        "BUILD_ENV_CONDA_ONLY",
        "WINDOWS_OS_COMPONENT",
        "MICROSOFT_SIGNED_PREREQUISITE",
        "APP_SHIPPED_THIRD_PARTY",
        "OCCT_OWNED",
        "OCP_SOURCE_BUILT",
    }
    if (
        runtime_policy.get("deployment_role") != "MICROSOFT_SIGNED_PREREQUISITE"
        or set(runtime_policy.get("deployment_roles", [])) != required_roles
        or runtime_policy.get("automatic_download") is not False
        or runtime_policy.get("minimum_version") != "14.44.35211.0"
        or runtime_contract.get("policy_path") != RUNTIME_POLICY.as_posix()
        or runtime_contract.get("policy_sha256") != sha256(RUNTIME_POLICY)
        or runtime_contract.get("minimum_vc_runtime_version") != runtime_policy["minimum_version"]
        or runtime_contract.get("deployment_roles") != runtime_policy["deployment_roles"]
        or runtime_contract.get("automatic_download") is not False
    ):
        raise ValueError("Windows native runtime deployment policy is incomplete or unsupported")
    lock = load_source_lock(LOCK)
    records = {row["id"]: row for row in lock["records"]}
    if sha256(LOCK) != args.expected_source_lock_sha256:
        raise ValueError("the checked-in source lock differs from the dispatched build identity")
    sdk = validate_sdk(
        args.occt_sdk,
        args.expected_run_id,
        args.expected_attempt,
        args.expected_cache_key,
        require_opengl=True,
    )
    sdk_source_lock_compatibility = validate_sdk_source_lock_compatibility(sdk, LOCK)
    sdk_toolchain_compatibility = validate_sdk_toolchain_contract_compatibility(sdk, CONTRACT)
    if sys.version.split()[0] != contract["target"]["python_version"]:
        raise ValueError("OCP producer Python differs from the frozen Windows contract")
    cmake_version = subprocess.check_output(["cmake", "--version"], text=True).splitlines()[0]
    if (
        cmake_version != contract["toolchain"]["cmake"]
        or _compiler_version(args.occt_sdk / "occt-sdk-metadata.json")
        != contract["toolchain"]["compiler"]
    ):
        raise ValueError("OCP producer toolchain differs from the sealed OCCT SDK contract")

    args.build_root.mkdir(parents=True, exist_ok=True)
    generated_root = args.build_root / "generated"
    patch_manifest = args.build_root / "generated-source-patch-manifest.json"
    patched = prepare_generated_sources(args.generated_source_zip, generated_root, patch_manifest)
    retained = set(patched["retained_modules"])
    if len(retained) != 315:
        raise ValueError("the No-VTK source preparation did not retain exactly 315 modules")
    if not REQUIRED_PACKLAB_MODULES <= retained:
        raise ValueError(
            "one or more literal PackLab OCP imports are absent from the retained module set"
        )
    dependency_audit = audit_dependencies(
        args.occt_sdk,
        args.generated_source_zip,
        args.occt_source_archive,
        args.build_root / "dependency-audit",
        expected_run_id=args.expected_run_id,
        expected_attempt=args.expected_attempt,
        expected_cache_key=args.expected_cache_key,
        require_opengl=True,
    )
    fmt_probe_path = args.build_root / "fmt-dependency-probe.json"
    _run(
        [
            "uv",
            "run",
            "--locked",
            "--no-sync",
            "python",
            "-m",
            "tools.packaging.probe_fmt_dependency",
            "--prefix",
            str(Path(sys.prefix)),
            "--scratch",
            str(args.build_root / "fmt-source-evidence"),
            "--generated-cmake",
            str(generated_root / "OCP_src_stubs_Windows" / "CMakeLists.txt"),
            "--report",
            str(fmt_probe_path),
            "--assert-pass",
        ]
    )
    fmt_probe = json.loads(fmt_probe_path.read_text(encoding="utf-8"))
    runtime_policy_evidence = validate_runtime(Path(sys.prefix), fmt_probe_path)

    occt_dlls = [path for path in args.occt_sdk.rglob("*.dll") if path.is_file()]
    occt_dlls_by_name = {path.name.casefold(): path for path in occt_dlls}
    if len(occt_dlls_by_name) != len(occt_dlls):
        raise ValueError("the sealed OCCT SDK has duplicate runtime DLL basenames")
    dll_directories = {path.parent for path in occt_dlls}
    config_matches = list(args.occt_sdk.rglob("OpenCASCADEConfig.cmake"))
    if not occt_dlls or len(dll_directories) != 1 or len(config_matches) != 1:
        raise ValueError("the sealed OCCT SDK is missing a flat DLL set or unique CMake package")
    expected_bin = args.occt_sdk / sdk["sdk_layout"]["binary_dir"]
    expected_lib = args.occt_sdk / sdk["sdk_layout"]["library_dir"]
    if dll_directories != {expected_bin} or not (expected_lib / "TKOpenGl.lib").is_file():
        raise ValueError("the sealed OCCT SDK DLL/LIB directories differ from its Windows layout")

    source_root = generated_root / "OCP_src_stubs_Windows"
    gl_include, _ = windows_sdk_gl_include_dir()
    cmake_build = args.build_root / "ocp-native-build"
    if cmake_build.exists():
        import shutil

        shutil.rmtree(cmake_build)
    if args.prebuilt_extension:
        quarantine_manifest_path = args.prebuilt_extension.parent / "quarantine-manifest.json"
        quarantine = json.loads(quarantine_manifest_path.read_text(encoding="utf-8"))
        expected_file = {
            "filename": args.prebuilt_extension.name,
            "sha256": sha256(args.prebuilt_extension),
            "byte_length": args.prebuilt_extension.stat().st_size,
        }
        source_revision = records[OCP_ID]["revision"]
        if (
            quarantine.get("status") != "QUARANTINED_NOT_REVIEWED_OR_DISTRIBUTABLE"
            or quarantine.get("artifact_role") != "POST_LINK_RECOVERY_EVIDENCE_ONLY"
            or quarantine.get("linked_extension_count") != 1
            or quarantine.get("files") != [expected_file]
            or quarantine.get("python") != sys.version.split()[0]
            or quarantine.get("python_abi")
            != f"cp{sys.version_info.major}{sys.version_info.minor}-win_amd64"
            or quarantine.get("ocp_source_revision") != source_revision
            or quarantine.get("occt_source_revision") != records[OCCT_ID]["revision"]
            or quarantine.get("sdk_payload_sha256") != sdk["payload_sha256"]
            or quarantine.get("source_lock_sha256") != sha256(LOCK)
        ):
            raise ValueError(
                "Prebuilt quarantine artifact does not match this source/ABI/SDK contract"
            )
        extensions = [args.prebuilt_extension]
        started = datetime.fromisoformat(args.prebuilt_build_started_utc)
        ended = datetime.fromisoformat(args.prebuilt_build_ended_utc)
        duration = float(args.prebuilt_build_duration_seconds)
        compile_evidence = {
            "mode": "REUSED_QUARANTINED_EXTENSION",
            "producer_run_id": args.prebuilt_producer_run_id,
            "producer_revision": args.prebuilt_producer_revision,
            "compiled_inputs_unchanged": True,
        }
    else:
        _run(
            [
                "cmake",
                "-S",
                str(source_root),
                "-B",
                str(cmake_build),
                "-G",
                GENERATOR,
                "-A",
                "x64",
                f"-DCMAKE_SYSTEM_VERSION={SDK_VERSION}",
                f"-DOpenCASCADE_DIR={config_matches[0].parent}",
                f"-DCMAKE_PREFIX_PATH={args.occt_sdk};{sys.prefix}",
                f"-DOCCT_LIB_DIR={next(iter(dll_directories))}",
                f"-DPython_EXECUTABLE={sys.executable}",
                f"-DOPENGL_INCLUDE_DIR={gl_include}",
            ]
        )
        started = datetime.now(UTC)
        monotonic_started = time.monotonic()
        _run(
            [
                "cmake",
                "--build",
                str(cmake_build),
                "--config",
                "Release",
                "--target",
                "OCP",
                "--parallel",
                str(PARALLELISM),
            ],
            timeout=args.compile_timeout_seconds,
        )
        ended = datetime.now(UTC)
        duration = round(time.monotonic() - monotonic_started, 3)
        extensions = [path for path in cmake_build.rglob("OCP*.pyd") if path.is_file()]
        compile_evidence = {"mode": "COLD_NATIVE_COMPILE", "compiled_inputs_unchanged": True}
    # Preserve the newly linked object before import-closure, packaging, or
    # compliance checks can fail. This artifact is quarantined evidence only.
    import shutil

    if extensions:
        args.quarantine_dir.mkdir(parents=True, exist_ok=False)
    quarantined_files = []
    for extension in extensions:
        quarantined_extension = args.quarantine_dir / extension.name
        shutil.copy2(extension, quarantined_extension)
        quarantined_files.append(
            {
                "filename": quarantined_extension.name,
                "sha256": sha256(quarantined_extension),
                "byte_length": quarantined_extension.stat().st_size,
            }
        )
    quarantine_manifest = {
        "schema_version": 1,
        "status": "QUARANTINED_NOT_REVIEWED_OR_DISTRIBUTABLE",
        "artifact_role": "POST_LINK_RECOVERY_EVIDENCE_ONLY",
        "linked_extension_count": len(quarantined_files),
        "files": quarantined_files,
        "python": sys.version.split()[0],
        "python_abi": f"cp{sys.version_info.major}{sys.version_info.minor}-win_amd64",
        "ocp_source_revision": records[OCP_ID]["revision"],
        "occt_source_revision": records[OCCT_ID]["revision"],
        "source_lock_sha256": sha256(LOCK),
        "sdk_payload_sha256": sdk["payload_sha256"],
        "sdk_source_lock_sha256": sdk["source_lock_sha256"],
        "sdk_toolchain_contract_sha256": sdk["toolchain_contract_sha256"],
        "build_started_utc": started.isoformat(),
        "build_ended_utc": ended.isoformat(),
        "build_duration_seconds": duration,
        "producer_run_id": args.expected_run_id
        if not args.prebuilt_extension
        else args.prebuilt_producer_run_id,
        "producer_revision": args.expected_source_lock_sha256
        if not args.prebuilt_extension
        else args.prebuilt_producer_revision,
    }
    if extensions:
        (args.quarantine_dir / "quarantine-manifest.json").write_text(
            json.dumps(quarantine_manifest, indent=2) + "\n", encoding="utf-8"
        )
        print(
            "OCP_POST_LINK_QUARANTINE_PASS "
            f"files={len(quarantined_files)} status={quarantine_manifest['status']}",
            flush=True,
        )
    if len(extensions) != 1 or not extensions[0].stem.startswith("OCP."):
        raise ValueError("generated-source C++ build did not produce exactly one OCP extension")

    fmt_dll = Path(sys.prefix) / "Library" / "bin" / "fmt.dll"
    fmt_record = records["fmt-source-12.1.0"]
    fmt_lock = fmt_probe["package_lock"]
    if (
        fmt_lock.get("sha256") != fmt_record["binary_package"]["sha256"]
        or fmt_lock.get("byte_length") != fmt_record["binary_package"]["byte_length"]
        or fmt_lock.get("dll_sha256")
        != "0d4edfe1411f4a7c5f57758239f0f1e6e1cff7f2d0ae5f9511a1dfacc08b388d"
        or not fmt_dll.is_file()
        or fmt_lock.get("dll_byte_length") != fmt_dll.stat().st_size
        or sha256(fmt_dll) != fmt_lock.get("dll_sha256")
    ):
        raise ValueError("The actual fmt DLL differs from its exact locked conda package evidence")
    pending = list(pe_imports(extensions[0]))
    required_dlls: set[str] = set()
    third_party_dlls: set[str] = set()
    external: set[str] = set()
    seen: set[str] = set()
    while pending:
        name = pending.pop().casefold()
        if name in seen:
            continue
        if is_external_runtime(name):
            external.add(name)
            seen.add(name)
            continue
        if is_windows_runtime_dll(name):
            external.add(name)
            seen.add(name)
            continue
        if name == "fmt.dll":
            third_party_dlls.add(name)
            seen.add(name)
            pending.extend(pe_imports(fmt_dll))
            continue
        dependency = occt_dlls_by_name.get(name)
        if dependency is None:
            raise ValueError(f"compiled OCP references an unowned DLL dependency: {name}")
        required_dlls.add(name)
        seen.add(name)
        pending.extend(pe_imports(dependency))

    args.site_packages.mkdir(parents=True, exist_ok=True)
    package = args.site_packages / "OCP"
    if package.exists():
        shutil.rmtree(package)
    package.mkdir()
    shutil.copy2(extensions[0], package / extensions[0].name)
    (package / "__init__.py").write_text(
        "from .OCP import *\nfrom .OCP import __version__\n", encoding="utf-8"
    )
    for name in sorted(required_dlls):
        shutil.copy2(occt_dlls_by_name[name], package / name)
    for name in sorted(third_party_dlls):
        shutil.copy2(fmt_dll, package / name)
    system32 = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32"
    resolved_external_imports = []
    for name in sorted(external):
        if name.startswith(("api-ms-win-", "ext-ms-win-")):
            host = resolve_windows_api_set_host(name, system32)
            resolved_external_imports.append(
                {
                    "name": name,
                    "deployment_role": "WINDOWS_OS_COMPONENT",
                    "resolved_host": host.name,
                    "host_sha256": sha256(host),
                }
            )
        elif name.startswith(("msvcp140", "vcruntime140", "concrt140", "vcomp140")):
            resolved_external_imports.append(
                {
                    "name": name,
                    "deployment_role": "MICROSOFT_SIGNED_PREREQUISITE",
                    "minimum_version": runtime_policy["minimum_version"],
                }
            )
        else:
            candidate = Path(sys.prefix) / name if name == "python312.dll" else system32 / name
            if not candidate.is_file():
                raise ValueError(
                    f"External native import did not resolve to its declared owner: {name}"
                )
            resolved_external_imports.append(
                {
                    "name": name,
                    "deployment_role": "PYTHON_RUNTIME"
                    if name == "python312.dll"
                    else "WINDOWS_OS_COMPONENT",
                    "resolved_path_class": "native_python_prefix"
                    if name == "python312.dll"
                    else "System32",
                    "resolved_sha256": sha256(candidate),
                }
            )

    compiler = _compiler_version(args.occt_sdk / "occt-sdk-metadata.json")
    toolchain = {
        "python": sys.version.split()[0],
        "cmake": cmake_version,
        "compiler": compiler,
        "windows_sdk": SDK_VERSION,
        "cmake_parallel": PARALLELISM,
        "cmake_generator": GENERATOR,
        "source_generation": "official-generated-windows-zip",
        "ocp_runtime_reported_version": patched["runtime_reported_version"],
        "ocp_release_version": "7.9.3.1.1",
    }
    occt_timing = {
        "phase": "occt_native_build",
        "started_utc": sdk["build_started_utc"],
        "ended_utc": sdk["build_ended_utc"],
        "duration_seconds": sdk["build_duration_seconds"],
        "worker_count": PARALLELISM,
    }
    ocp_timing = {
        "phase": "ocp_native_compile_link",
        "started_utc": started.isoformat(),
        "ended_utc": ended.isoformat(),
        "duration_seconds": duration,
        "worker_count": PARALLELISM,
    }
    file_records = []
    for path in sorted(package.iterdir()):
        if path.suffix.casefold() not in {".pyd", ".dll"}:
            continue
        source_id = (
            OCP_ID
            if path.suffix.casefold() == ".pyd"
            else "fmt-source-12.1.0"
            if path.name.casefold() == "fmt.dll"
            else OCCT_ID
        )
        source = records[source_id]
        file_records.append(
            {
                "relative_path": f"OCP/{path.name}",
                "sha256": sha256(path),
                "owning_component": source["component"],
                "source_package_id": source_id,
                "version": source["version"],
                "build_revision": source["revision"],
                "license_identifier": source["license_identifier"],
                "license_notice_source": source["license_notice_source"],
                "production_purpose": "PackLab CAD binding or transitive OCCT runtime dependency",
                "deployment_role": (
                    "OCP_SOURCE_BUILT"
                    if source_id == OCP_ID
                    else "APP_SHIPPED_THIRD_PARTY"
                    if source_id == "fmt-source-12.1.0"
                    else "OCCT_OWNED"
                ),
                **(
                    {
                        "binary_package": fmt_record["binary_package"],
                        "binary_sha256": fmt_lock["dll_sha256"],
                        "binary_byte_length": fmt_lock["dll_byte_length"],
                        "recipe": fmt_record["recipe"],
                    }
                    if source_id == "fmt-source-12.1.0"
                    else {}
                ),
            }
        )
    manifest = {
        "schema_version": 1,
        "status": "PASS",
        "input_lock_sha256": sha256(LOCK),
        "ocp_source_revision": records[OCP_ID]["revision"],
        "occt_source_revision": records[OCCT_ID]["revision"],
        "source_method": "official-generated-source-zip-no-pywrap",
        "generated_source": {
            "archive_sha256": patched["source_archive"]["sha256"],
            "archive_byte_length": patched["source_archive"]["byte_length"],
            "patch_manifest_sha256": sha256(patch_manifest),
            "patch_manifest": patch_manifest.name,
            "input_module_count": patched["input_module_count"],
            "output_module_count": patched["output_module_count"],
            "removed_modules": patched["removed_modules"],
            "retained_modules": patched["retained_modules"],
            "runtime_reported_version": patched["runtime_reported_version"],
            "pywrap_generation_invoked": False,
        },
        "occt_sdk_checkpoint": {
            "producer_run_id": sdk["producer_run_id"],
            "producer_run_attempt": sdk["producer_run_attempt"],
            "manifest_sha256": sha256(args.occt_sdk / "occt-sdk-metadata.json"),
            "payload_sha256": sdk["payload_sha256"],
            "byte_count": sdk["byte_count"],
            "file_count": sdk["file_count"],
            "source_lock_sha256": sdk["source_lock_sha256"],
            "source_lock_compatibility": sdk_source_lock_compatibility,
            "toolchain_contract_sha256": sdk["toolchain_contract_sha256"],
            "toolchain_contract_compatibility": sdk_toolchain_compatibility,
        },
        "occt_sdk_dependency_audit": dependency_audit,
        "windows_runtime_deployment": {
            "policy_path": RUNTIME_POLICY.as_posix(),
            "policy_sha256": sha256(RUNTIME_POLICY),
            "deployment_roles": runtime_contract["deployment_roles"],
            "minimum_vc_runtime_version": runtime_contract["minimum_vc_runtime_version"],
            "automatic_download": runtime_contract["automatic_download"],
        },
        "windows_runtime_policy_evidence": runtime_policy_evidence,
        "toolchain": toolchain,
        "build_timings": [occt_timing, ocp_timing],
        "compile_evidence": compile_evidence,
        "external_runtime_dependencies": sorted(external),
        "native_import_ownership": {
            "fmt": {
                "source_package_id": "fmt-source-12.1.0",
                "deployment_role": "APP_SHIPPED_THIRD_PARTY",
                "binary_package": fmt_record["binary_package"],
                "binary_sha256": fmt_lock["dll_sha256"],
                "source_revision": fmt_record["revision"],
                "license_identifier": fmt_record["license_identifier"],
                "license_notice_source": fmt_record["license_notice_source"],
                "license_notice_sha256": fmt_record["license_notice_sha256"],
                "recipe": fmt_record["recipe"],
            },
            "windows_os_and_vc_prerequisite_imports": sorted(external),
            "resolved_external_imports": resolved_external_imports,
        },
        "files": file_records,
    }
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generated-source-zip", required=True, type=Path)
    parser.add_argument("--occt-source-archive", required=True, type=Path)
    parser.add_argument("--occt-sdk", required=True, type=Path)
    parser.add_argument("--expected-run-id", required=True)
    parser.add_argument("--expected-attempt", required=True)
    parser.add_argument("--expected-cache-key", required=True)
    parser.add_argument("--expected-source-lock-sha256", required=True)
    parser.add_argument("--build-root", required=True, type=Path)
    parser.add_argument("--site-packages", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--quarantine-dir", required=True, type=Path)
    parser.add_argument("--prebuilt-extension", type=Path)
    parser.add_argument("--prebuilt-producer-run-id")
    parser.add_argument("--prebuilt-producer-revision")
    parser.add_argument("--prebuilt-build-started-utc")
    parser.add_argument("--prebuilt-build-ended-utc")
    parser.add_argument("--prebuilt-build-duration-seconds", type=float)
    parser.add_argument("--compile-timeout-seconds", type=int, default=MAX_COMPILE_SECONDS)
    args = parser.parse_args()
    if args.prebuilt_extension and not all(
        (
            args.prebuilt_producer_run_id,
            args.prebuilt_producer_revision,
            args.prebuilt_build_started_utc,
            args.prebuilt_build_ended_utc,
            args.prebuilt_build_duration_seconds,
        )
    ):
        parser.error("prebuilt reuse requires run, revision, and original timing evidence")
    if args.compile_timeout_seconds <= 0 or args.compile_timeout_seconds > MAX_COMPILE_SECONDS:
        raise ValueError("native compile timeout exceeds the 270-minute safety budget")
    result = build_from_generated_sources(args)
    print(
        "CONTROLLED_OCP_315_NATIVE_BUILD_PASS "
        f"modules={result['generated_source']['output_module_count']} "
        f"compile_seconds={result['build_timings'][1]['duration_seconds']} "
        f"pywrap={result['generated_source']['pywrap_generation_invoked']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
