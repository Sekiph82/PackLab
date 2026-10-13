from __future__ import annotations

import json
from pathlib import Path

import pytest
from tools.packaging.windows_native_runtime_policy import (
    deployment_role,
    is_windows_runtime_dll,
    minimum_runtime_version,
    runtime_is_supported,
    version_below_minimum,
)
from tools.packaging.windows_sdk_source_lock_compatibility import (
    validate_sdk_source_lock_compatibility,
    validate_sdk_toolchain_contract_compatibility,
)

ROOT = Path(__file__).resolve().parents[2]
SOURCE_LOCK = ROOT / "tools/packaging/windows_native_source_lock.json"
PREREQUISITE = ROOT / "tools/packaging/windows-runtime-prerequisite.json"
INSTALLER = ROOT / "tools/packaging/PackLabStudio.iss"
LEGACY_SHA = "c6a32326c1463dce53a70366200e9739d853893030f0553739188d878b1bf277"
LEGACY_TOOLCHAIN_SHA = "45573da96fd6f0bb8b6066521c9cdebaad4bd3f808eb8a7dc328e603bd1b44df"


def test_runtime_classification_covers_os_and_vc_payloads() -> None:
    for name in (
        "api-ms-win-core-file-l1-1-0.dll",
        "ext-ms-win-ntuser-window-l1-1-0.dll",
        "ucrtbase.dll",
        "msvcp140.dll",
        "msvcp140_1.dll",
        "msvcp140_atomic_wait.dll",
        "vcruntime140.dll",
        "vcruntime140_1.dll",
        "vcruntime140_threads.dll",
        "ucrtbase_clr0400.dll",
        "concrt140.dll",
        "vcomp140.dll",
    ):
        assert is_windows_runtime_dll(Path("nested") / name)
    assert not is_windows_runtime_dll("fmt.dll")
    assert deployment_role("vc14_runtime") == "BUILD_ENV_CONDA_ONLY"
    assert deployment_role("ucrt") == "BUILD_ENV_CONDA_ONLY"
    assert deployment_role("fmt") is None


def test_api_set_policy_resolves_through_windows_os_loader() -> None:
    validator = (ROOT / "tools/packaging/validate_windows_native_runtime_policy.py").read_text(
        encoding="utf-8"
    )
    assert "LoadLibraryW" in validator
    assert "GetModuleFileNameW" in validator
    assert '"resolved_host": path.name' in validator
    assert '"deployment_role": "WINDOWS_OS_COMPONENT"' in validator


def test_prerequisite_gate_rejects_missing_wrong_arch_and_undersized() -> None:
    policy = json.loads(PREREQUISITE.read_text(encoding="utf-8"))
    minimum = minimum_runtime_version(policy)
    assert runtime_is_supported(
        installed=True, architecture="x64", version=(14, 44, 35211, 0), minimum=minimum
    )
    assert not runtime_is_supported(
        installed=False, architecture="x64", version=(14, 50, 35710, 0), minimum=minimum
    )
    assert not runtime_is_supported(
        installed=True, architecture="x86", version=(14, 50, 35710, 0), minimum=minimum
    )
    assert not runtime_is_supported(
        installed=True, architecture="x64", version=(14, 44, 35210, 9), minimum=minimum
    )
    assert version_below_minimum(minimum) < minimum
    assert not runtime_is_supported(
        installed=True,
        architecture="x64",
        version=version_below_minimum(minimum),
        minimum=minimum,
    )


def test_inno_prerequisite_gate_uses_contract_architecture_and_version_fields() -> None:
    policy = json.loads(PREREQUISITE.read_text(encoding="utf-8"))
    minimum = minimum_runtime_version(policy)
    installer = INSTALLER.read_text(encoding="utf-8")
    assert "RegQueryDWordValue(HKLM64" in installer
    assert "'SOFTWARE\\Microsoft\\VisualStudio\\14.0\\VC\\Runtimes\\x64'" in installer
    assert all(f"'{name}'" in installer for name in ("Installed", "Major", "Minor", "Bld", "Rbld"))
    assert f"(Minor = {minimum[1]})" in installer
    assert f"(Build > {minimum[2]})" in installer
    assert "does not download it automatically" in installer
    assert runtime_is_supported(
        installed=True, architecture="x64", version=minimum, minimum=minimum
    )
    assert not runtime_is_supported(
        installed=True, architecture="x86", version=minimum, minimum=minimum
    )


def test_sdk_source_lock_bridge_accepts_only_frozen_origin_projection(tmp_path: Path) -> None:
    lock = json.loads(SOURCE_LOCK.read_text(encoding="utf-8"))
    lock_path = tmp_path / "source-lock.json"
    lock_path.write_text(json.dumps(lock), encoding="utf-8")
    result = validate_sdk_source_lock_compatibility({"source_lock_sha256": LEGACY_SHA}, lock_path)
    assert result["mode"] == "R04_ORIGIN_COMPATIBLE"

    lock["records"] = [row for row in lock["records"] if row["id"] != "fmt-source-12.1.0"]
    lock_path.write_text(json.dumps(lock), encoding="utf-8")
    assert (
        validate_sdk_source_lock_compatibility({"source_lock_sha256": LEGACY_SHA}, lock_path)[
            "mode"
        ]
        == "R04_ORIGIN_COMPATIBLE"
    )

    lock["records"][0]["sha256"] = "0" * 64
    lock_path.write_text(json.dumps(lock), encoding="utf-8")
    with pytest.raises(ValueError, match="SDK-relevant source inputs differ"):
        validate_sdk_source_lock_compatibility({"source_lock_sha256": LEGACY_SHA}, lock_path)


def test_sdk_source_lock_bridge_rejects_unrecognized_origin(tmp_path: Path) -> None:
    lock_path = tmp_path / "source-lock.json"
    lock_path.write_bytes(SOURCE_LOCK.read_bytes())
    with pytest.raises(ValueError, match="neither current nor approved R04"):
        validate_sdk_source_lock_compatibility({"source_lock_sha256": "f" * 64}, lock_path)


def test_sdk_toolchain_contract_bridge_preserves_r04_identity(tmp_path: Path) -> None:
    contract = json.loads(
        (ROOT / "tools/packaging/controlled_ocp_runtime_contract.json").read_text(encoding="utf-8")
    )
    path = tmp_path / "runtime-contract.json"
    path.write_text(json.dumps(contract), encoding="utf-8")
    result = validate_sdk_toolchain_contract_compatibility(
        {"toolchain_contract_sha256": LEGACY_TOOLCHAIN_SHA}, path
    )
    assert result["mode"] == "R04_ORIGIN_COMPATIBLE"

    contract["toolchain"]["compiler"] = "MSVC 19.50.35710.0"
    path.write_text(json.dumps(contract), encoding="utf-8")
    with pytest.raises(ValueError, match="SDK toolchain inputs differ"):
        validate_sdk_toolchain_contract_compatibility(
            {"toolchain_contract_sha256": LEGACY_TOOLCHAIN_SHA}, path
        )
