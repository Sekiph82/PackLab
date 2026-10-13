"""Fail-closed bidirectional validation for the generated controlled OCP manifest."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path, PurePosixPath
from typing import Any

from tools.packaging.validate_windows_native_source_lock import load_source_lock
from tools.packaging.windows_native_runtime_policy import is_windows_runtime_dll
from tools.packaging.windows_sdk_source_lock_compatibility import (
    validate_sdk_source_lock_compatibility,
    validate_sdk_toolchain_contract_compatibility,
)

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SOURCE_COMPONENTS = {
    "ocp-source-7.9.3.1.1": "OCP",
    "occt-source-7.9.3": "OCCT",
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
    return manifest


def validate_staged_tree(stage_root: Path, manifest: dict[str, Any]) -> None:
    stage_root = stage_root.resolve(strict=True)
    expected = {entry["relative_path"]: entry for entry in manifest["files"]}
    observed: dict[str, Path] = {}
    for path in stage_root.rglob("*"):
        if not path.is_file():
            continue
        if is_windows_runtime_dll(path):
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
            raise ValueError("An OCP native file is staged without controlled provenance")
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
