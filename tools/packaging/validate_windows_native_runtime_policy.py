"""Validate hosted Windows runtime roles, API-set resolution, and installer policy."""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import platform
import sys
from pathlib import Path
from typing import Any

from tools.packaging.probe_fmt_dependency import package_lock_rows
from tools.packaging.windows_native_runtime_policy import (
    is_windows_runtime_dll,
    minimum_runtime_version,
    runtime_is_supported,
)

POLICY = Path("tools/packaging/windows-runtime-prerequisite.json")
INSTALLER = Path("tools/packaging/PackLabStudio.iss")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def installed_vc_runtime() -> tuple[tuple[int, ...], dict[str, int]]:
    if os.name != "nt" or platform.machine().casefold() not in {"amd64", "x86_64"}:
        raise ValueError("The target must be a native x64 Windows runner")
    import winreg

    subkey = r"SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64"
    with winreg.OpenKey(
        winreg.HKEY_LOCAL_MACHINE,
        subkey,
        0,
        winreg.KEY_READ | winreg.KEY_WOW64_64KEY,
    ) as key:
        fields = {
            name: int(winreg.QueryValueEx(key, name)[0])
            for name in ("Installed", "Major", "Minor", "Bld", "Rbld")
        }
    version = (
        fields["Major"],
        fields["Minor"],
        fields["Bld"],
        fields["Rbld"],
    )
    return version, fields


def resolve_windows_api_set_host(name: str, system32: Path) -> Path:
    """Resolve a Windows API-set contract through the OS loader to its host DLL."""
    if os.name != "nt":
        raise ValueError("Windows API-set contracts can only be resolved on Windows")
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    load_library = kernel32.LoadLibraryW
    load_library.argtypes = [wintypes.LPCWSTR]
    load_library.restype = wintypes.HMODULE
    get_module_file_name = kernel32.GetModuleFileNameW
    get_module_file_name.argtypes = [wintypes.HMODULE, wintypes.LPWSTR, wintypes.DWORD]
    get_module_file_name.restype = wintypes.DWORD
    free_library = kernel32.FreeLibrary
    free_library.argtypes = [wintypes.HMODULE]
    free_library.restype = wintypes.BOOL

    handle = load_library(name)
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        buffer = ctypes.create_unicode_buffer(32768)
        length = get_module_file_name(handle, buffer, len(buffer))
        if length == 0 or length >= len(buffer):
            raise ctypes.WinError(ctypes.get_last_error())
        host = Path(buffer.value).resolve(strict=True)
    finally:
        free_library(handle)
    if host.parent != system32.resolve(strict=True) or not host.is_file():
        raise ValueError(f"API-set contract {name} did not resolve to a System32 host DLL: {host}")
    return host


def validate_runtime(prefix: Path, fmt_probe: Path, stage: Path | None = None) -> dict[str, Any]:
    prefix = prefix.resolve(strict=True)
    if Path(sys.prefix).resolve() != prefix or sys.version_info[:3] != (3, 12, 15):
        raise ValueError("Runtime policy diagnostic must run inside native conda Python 3.12.15")
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    minimum = minimum_runtime_version(policy)
    installer = INSTALLER.read_text(encoding="utf-8")
    for fragment in (
        "RegQueryDWordValue(HKLM64",
        "'Installed'",
        "'Major'",
        "'Minor'",
        "'Bld'",
        "'Rbld'",
        "PackLab does not download it automatically",
    ):
        if fragment not in installer:
            raise ValueError(f"Inno Setup prerequisite gate is missing {fragment!r}")
    probe = json.loads(fmt_probe.read_text(encoding="utf-8"))
    if probe.get("status") != "PASS":
        raise ValueError("The locked fmt import-closure probe is not passing")
    system_root = Path(os.environ.get("SystemRoot", r"C:\Windows"))
    system32 = system_root / "System32"
    api_sets = sorted(
        {
            row["name"].casefold()
            for row in probe.get("native_import_closure", [])
            if row.get("name", "").casefold().startswith(("api-ms-win-", "ext-ms-win-"))
        }
    )
    if not api_sets:
        raise ValueError("fmt probe did not enumerate any API-set imports")
    locked_packages = package_lock_rows(Path("tools/packaging/packlab-ocp-bindings-win.lock"))
    build_environment_only = []
    for package_name in policy["build_environment_packages"]:
        locked = locked_packages.get(package_name.casefold())
        installed_records = list((prefix / "conda-meta").glob(f"{package_name}-*.json"))
        if locked is None or len(installed_records) != 1:
            raise ValueError(f"Expected one exact locked build-only package record: {package_name}")
        installed = json.loads(installed_records[0].read_text(encoding="utf-8"))
        if any(
            installed.get(field) != locked.get(key)
            for field, key in (
                ("name", "name"),
                ("version", "version"),
                ("build", "build"),
                ("url", "url"),
            )
        ):
            raise ValueError(
                f"Build-only conda package differs from the frozen lock: {package_name}"
            )
        build_environment_only.append(
            {
                "name": package_name,
                "version": locked["version"],
                "build": locked["build"],
                "deployment_role": "BUILD_ENV_CONDA_ONLY",
                "archive_sha256": locked["hash"]["sha256"],
            }
        )
    api_set_records = []
    for name in api_sets:
        path = resolve_windows_api_set_host(name, system32)
        api_set_records.append(
            {
                "name": name,
                "resolved_host": path.name,
                "deployment_role": "WINDOWS_OS_COMPONENT",
                "host_sha256": sha256(path),
            }
        )
    version, fields = installed_vc_runtime()
    vc_installed = fields["Installed"] == 1
    if not runtime_is_supported(
        installed=vc_installed, architecture="x64", version=version, minimum=minimum
    ):
        raise ValueError(
            "Hosted x64 VC Redistributable is missing, wrong-architecture, or below minimum"
        )
    negative_cases = {
        "missing": runtime_is_supported(
            installed=False, architecture="x64", version=version, minimum=minimum
        ),
        "wrong_architecture": runtime_is_supported(
            installed=True, architecture="x86", version=version, minimum=minimum
        ),
        "below_minimum": runtime_is_supported(
            installed=True,
            architecture="x64",
            version=tuple(
                max(0, value - (1 if index == len(minimum) - 1 else 0))
                for index, value in enumerate(minimum)
            ),
            minimum=minimum,
        ),
    }
    if any(negative_cases.values()):
        raise ValueError("VC Redistributable negative prerequisite simulations did not fail closed")
    staged_runtime = []
    if stage is not None:
        staged_runtime = [
            path.relative_to(stage).as_posix()
            for path in stage.rglob("*")
            if path.is_file() and is_windows_runtime_dll(path)
        ]
        if staged_runtime:
            raise ValueError(
                f"Windows runtime copies are staged in the app payload: {staged_runtime[:12]}"
            )
    return {
        "schema_version": 1,
        "status": "PASS",
        "target_architecture": platform.machine(),
        "windows_os_component_policy": policy["windows_os_component_policy"],
        "vc_runtime": {
            "deployment_role": policy["deployment_role"],
            "installed_fields": fields,
            "version": ".".join(str(part) for part in version),
            "minimum_version": policy["minimum_version"],
        },
        "negative_prerequisite_simulations": negative_cases,
        "api_set_system32_components": api_set_records,
        "build_environment_only_packages": build_environment_only,
        "staged_windows_runtime_files": staged_runtime,
        "prerequisite_policy_sha256": sha256(POLICY),
        "installer_sha256": sha256(INSTALLER),
        "python": sys.version.split()[0],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prefix", type=Path, required=True)
    parser.add_argument("--fmt-probe", type=Path, required=True)
    parser.add_argument("--stage", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    report = validate_runtime(args.prefix, args.fmt_probe, args.stage)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        f"WINDOWS_NATIVE_RUNTIME_POLICY_PASS vc={report['vc_runtime']['version']} api_sets={len(report['api_set_system32_components'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
