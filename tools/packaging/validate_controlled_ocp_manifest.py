"""Fail-closed bidirectional validation for the generated controlled OCP manifest."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path, PurePosixPath
from typing import Any

from tools.packaging.validate_windows_native_source_lock import load_source_lock
from tools.packaging.windows_native_runtime_policy import (
    is_numpy_wheel_msvc_alias,
    is_windows_runtime_dll,
)
from tools.packaging.windows_sdk_source_lock_compatibility import (
    validate_sdk_source_lock_compatibility,
    validate_sdk_toolchain_contract_compatibility,
)

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SOURCE_COMPONENTS = {
    "ocp-source-7.9.3.1.1": "OCP",
    "occt-source-7.9.3": "OCCT",
    "fmt-source-12.1.0": "fmt native dependency",
}
RUNTIME_POLICY = Path("tools/packaging/windows-runtime-prerequisite.json")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_and_validate_manifest(manifest_path: Path, source_lock_path: Path) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    lock = load_source_lock(source_lock_path)
    if manifest.get("schema_version") != 1 or manifest.get("status") != "PASS":
        raise ValueError("Controlled OCP manifest is not passing")
    if manifest.get("input_lock_sha256") != sha256(source_lock_path):
        raise ValueError("Controlled OCP manifest is not bound to the checked-in source lock")
    sdk_checkpoint = manifest.get("occt_sdk_checkpoint")
    if not isinstance(sdk_checkpoint, dict):
        raise ValueError("Controlled OCP manifest has no sealed OCCT SDK identity")
    compatibility = validate_sdk_source_lock_compatibility(
        {"source_lock_sha256": sdk_checkpoint.get("source_lock_sha256")}, source_lock_path
    )
    if sdk_checkpoint.get("source_lock_compatibility") != compatibility:
        raise ValueError("Controlled OCP manifest changed the OCCT SDK source-lock lineage")
    toolchain_compatibility = validate_sdk_toolchain_contract_compatibility(
        {"toolchain_contract_sha256": sdk_checkpoint.get("toolchain_contract_sha256")}
    )
    if sdk_checkpoint.get("toolchain_contract_compatibility") != toolchain_compatibility:
        raise ValueError("Controlled OCP manifest changed the OCCT SDK toolchain-contract lineage")
    deployment = manifest.get("windows_runtime_deployment")
    policy = json.loads(RUNTIME_POLICY.read_text(encoding="utf-8"))
    if (
        not isinstance(deployment, dict)
        or deployment.get("policy_path") != RUNTIME_POLICY.as_posix()
        or deployment.get("policy_sha256") != sha256(RUNTIME_POLICY)
        or deployment.get("deployment_roles") != policy.get("deployment_roles")
        or deployment.get("minimum_vc_runtime_version") != policy.get("minimum_version")
        or deployment.get("automatic_download") is not False
    ):
        raise ValueError(
            "Controlled OCP manifest is not bound to the Windows runtime deployment policy"
        )
    runtime_evidence = manifest.get("windows_runtime_policy_evidence")
    if (
        not isinstance(runtime_evidence, dict)
        or runtime_evidence.get("status") != "PASS"
        or runtime_evidence.get("prerequisite_policy_sha256") != sha256(RUNTIME_POLICY)
        or runtime_evidence.get("vc_runtime", {}).get("deployment_role")
        != "MICROSOFT_SIGNED_PREREQUISITE"
        or runtime_evidence.get("negative_prerequisite_simulations")
        != {"missing": False, "wrong_architecture": False, "below_minimum": False}
    ):
        raise ValueError("Controlled OCP manifest lacks passing hosted Windows runtime evidence")
    records = {record["id"]: record for record in lock["records"]}
    entries = manifest.get("files")
    if not isinstance(entries, list) or not entries:
        raise ValueError("Controlled OCP manifest must contain native-file records")
    seen: set[str] = set()
    for entry in entries:
        relative = entry.get("relative_path")
        source_id = entry.get("source_package_id")
        path = PurePosixPath(relative) if isinstance(relative, str) else None
        if (
            path is None
            or path.is_absolute()
            or path.parts[0:1] != ("OCP",)
            or ".." in path.parts
            or path.suffix.casefold() not in {".pyd", ".dll"}
            or not SHA256_RE.fullmatch(entry.get("sha256", ""))
            or source_id not in SOURCE_COMPONENTS
        ):
            raise ValueError("Controlled OCP manifest contains an invalid native-file record")
        if relative in seen:
            raise ValueError("Controlled OCP manifest contains a duplicate relative path")
        seen.add(relative)
        record = records[source_id]
        expected_component = SOURCE_COMPONENTS[source_id]
        expected_extension = ".pyd" if expected_component == "OCP" else ".dll"
        if (
            entry.get("owning_component") != expected_component
            or path.suffix.casefold() != expected_extension
            or entry.get("version") != record["version"]
            or entry.get("build_revision") != record.get("revision")
            or entry.get("license_identifier") != record["license_identifier"]
            or entry.get("license_notice_source") != record["license_notice_source"]
        ):
            raise ValueError("Controlled OCP file provenance differs from its exact source lock")
        expected_role = {
            "OCP": "OCP_SOURCE_BUILT",
            "OCCT": "OCCT_OWNED",
            "fmt native dependency": "APP_SHIPPED_THIRD_PARTY",
        }[expected_component]
        if entry.get("deployment_role") != expected_role:
            raise ValueError("Controlled OCP file has an invalid deployment ownership role")
        if expected_component == "fmt native dependency":
            package = record.get("binary_package", {})
            if (
                relative.casefold() != "ocp/fmt.dll"
                or entry.get("binary_sha256")
                != "0d4edfe1411f4a7c5f57758239f0f1e6e1cff7f2d0ae5f9511a1dfacc08b388d"
                or not isinstance(entry.get("binary_byte_length"), int)
                or entry.get("binary_byte_length", 0) <= 0
                or entry.get("binary_package") != package
                or entry.get("recipe") != record.get("recipe")
            ):
                raise ValueError("fmt.dll is not bound to the exact locked package and recipe")
    fmt_record = records["fmt-source-12.1.0"]
    ownership = manifest.get("native_import_ownership")
    fmt_ownership = ownership.get("fmt") if isinstance(ownership, dict) else None
    if (
        not isinstance(fmt_ownership, dict)
        or fmt_ownership.get("source_package_id") != "fmt-source-12.1.0"
        or fmt_ownership.get("deployment_role") != "APP_SHIPPED_THIRD_PARTY"
        or fmt_ownership.get("binary_package") != fmt_record.get("binary_package")
        or fmt_ownership.get("binary_sha256")
        != "0d4edfe1411f4a7c5f57758239f0f1e6e1cff7f2d0ae5f9511a1dfacc08b388d"
        or fmt_ownership.get("source_revision") != fmt_record.get("revision")
        or fmt_ownership.get("license_identifier") != fmt_record.get("license_identifier")
        or fmt_ownership.get("license_notice_source") != fmt_record.get("license_notice_source")
        or fmt_ownership.get("license_notice_sha256") != fmt_record.get("license_notice_sha256")
        or fmt_ownership.get("recipe") != fmt_record.get("recipe")
        or "OCP/fmt.dll" not in seen
    ):
        raise ValueError("The final PE dependency graph does not carry exact fmt source ownership")
    external = ownership.get("windows_os_and_vc_prerequisite_imports", [])
    if not isinstance(external, list) or any(
        not isinstance(item, str) or item.casefold() == "fmt.dll" for item in external
    ):
        raise ValueError(
            "The final PE dependency graph has an invalid external-runtime classification"
        )
    resolved = ownership.get("resolved_external_imports")
    if (
        not isinstance(resolved, list)
        or any(not isinstance(item, dict) for item in resolved)
        or sorted(item.get("name", "").casefold() for item in resolved) != sorted(external)
    ):
        raise ValueError("The final PE external imports are not completely resolved to owners")
    for item in resolved:
        name = item.get("name", "").casefold()
        role = item.get("deployment_role")
        if name.startswith(("api-ms-win-", "ext-ms-win-")):
            if (
                role != "WINDOWS_OS_COMPONENT"
                or not item.get("resolved_host")
                or not SHA256_RE.fullmatch(item.get("host_sha256", ""))
            ):
                raise ValueError("A Windows API-set import lacks its resolved OS host identity")
        elif name.startswith(("msvcp140", "vcruntime140", "concrt140", "vcomp140")):
            if role != "MICROSOFT_SIGNED_PREREQUISITE" or item.get("minimum_version") != policy.get(
                "minimum_version"
            ):
                raise ValueError("A Microsoft runtime import lacks the signed prerequisite gate")
        elif role == "PYTHON_RUNTIME":
            if name != "python312.dll" or item.get("resolved_path_class") != "native_python_prefix":
                raise ValueError("A Python runtime import has an invalid owner identity")
        elif (
            role != "WINDOWS_OS_COMPONENT"
            or item.get("resolved_path_class") != "System32"
            or not SHA256_RE.fullmatch(item.get("resolved_sha256", ""))
        ):
            raise ValueError("A Windows system import lacks its hashed System32 owner identity")
    return manifest


def validate_staged_tree(stage_root: Path, manifest: dict[str, Any]) -> None:
    stage_root = stage_root.resolve(strict=True)
    expected = {entry["relative_path"]: entry for entry in manifest["files"]}
    observed: dict[str, Path] = {}
    for path in stage_root.rglob("*"):
        if not path.is_file():
            continue
        if is_windows_runtime_dll(path) and not is_numpy_wheel_msvc_alias(
            path.relative_to(stage_root)
        ):
            raise ValueError(
                "A Windows OS or VC prerequisite runtime DLL is staged in the application payload"
            )
        if path.suffix.casefold() not in {".pyd", ".dll"}:
            continue
        relative = path.relative_to(stage_root).as_posix()
        lowered = relative.casefold()
        marker = "/ocp/"
        if marker not in f"/{lowered}":
            continue
        suffix = relative[relative.casefold().find(marker) + 1 :]
        if suffix in observed:
            raise ValueError("A controlled OCP native file was staged more than once")
        observed[suffix] = path
        if suffix not in expected:
            raise ValueError(
                "An OCP native file is staged without controlled provenance: " + path.name
            )
    if set(observed) != set(expected):
        raise ValueError("The controlled OCP manifest and staged native files differ")
    for relative, path in observed.items():
        if sha256(path) != expected[relative]["sha256"]:
            raise ValueError("A staged controlled OCP native file differs from its manifest hash")


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument(
        "--source-lock", type=Path, default=Path("tools/packaging/windows_native_source_lock.json")
    )
    parser.add_argument("--stage", type=Path, required=True)
    args = parser.parse_args()
    manifest = load_and_validate_manifest(args.manifest, args.source_lock)
    validate_staged_tree(args.stage, manifest)
    print(
        f"CONTROLLED_OCP_MANIFEST_PASS files={len(manifest['files'])} sha256={sha256(args.manifest)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
