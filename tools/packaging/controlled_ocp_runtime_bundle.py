"""Seal, validate, install, and smoke-test the controlled OCP runtime bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any

from tools.packaging.validate_controlled_ocp_manifest import (
    load_and_validate_manifest,
    validate_staged_tree,
)
from tools.packaging.validate_windows_native_source_lock import load_source_lock

BUNDLE_SCHEMA_VERSION = 1
METADATA_NAME = "controlled-runtime-metadata.json"
MANIFEST_NAME = "windows-ocp-controlled-runtime-manifest.json"
SOURCE_EVIDENCE_NAME = "windows-native-source-evidence.json"
MANIFEST_VALIDATOR = Path(__file__).with_name("validate_controlled_ocp_manifest.py")
SOURCE_LOCK_VALIDATOR = Path(__file__).with_name("validate_windows_native_source_lock.py")
SOURCE_FETCHER = Path(__file__).with_name("fetch_verify_windows_native_sources.py")
BUILDER = Path(__file__).with_name("build_controlled_ocp_runtime.py")
RUNNER_PATH_RE = re.compile(r"(?i)(?<![a-z])[a-z]:[\\/]|/(?:home|runner)/")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def read_json(path: Path, description: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"{description} is missing or invalid JSON") from error
    if not isinstance(value, dict):
        raise ValueError(f"{description} must be a JSON object")
    return value


def reject_runner_paths(paths: list[Path]) -> None:
    for path in paths:
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if RUNNER_PATH_RE.search(content):
            raise ValueError("Controlled-runtime bundle evidence contains an absolute runner path")


def runtime_inventory(ocp_root: Path) -> list[dict[str, Any]]:
    if not ocp_root.is_dir() or ocp_root.is_symlink():
        raise ValueError("The controlled bundle must contain a regular OCP directory")
    records: list[dict[str, Any]] = []
    seen_casefold: set[str] = set()
    for path in sorted(ocp_root.rglob("*")):
        if path.is_symlink():
            raise ValueError("The controlled OCP runtime cannot contain symbolic links")
        if not path.is_file():
            continue
        relative = path.relative_to(ocp_root.parent).as_posix()
        normalized = PurePosixPath(relative)
        if normalized.is_absolute() or ".." in normalized.parts:
            raise ValueError("The controlled OCP runtime contains an unsafe path")
        if relative.casefold() in seen_casefold:
            raise ValueError("The controlled OCP runtime contains case-insensitive duplicate paths")
        seen_casefold.add(relative.casefold())
        records.append(
            {
                "relative_path": relative,
                "sha256": sha256(path),
                "byte_length": path.stat().st_size,
            }
        )
    if not records:
        raise ValueError("The controlled OCP runtime bundle is empty")
    return records


def validate_source_evidence(evidence_path: Path, source_lock_path: Path) -> dict[str, Any]:
    evidence = read_json(evidence_path, "Corresponding-source evidence")
    lock = load_source_lock(source_lock_path)
    lock_digest = sha256(source_lock_path)
    expected = {
        record["id"]: record
        for record in lock["records"]
        if record["source_availability_role"]
        in {
            "SOURCE_BUILD_INPUT",
            "CORRESPONDING_SOURCE_AND_NOTICES",
            "CORRESPONDING_SOURCE_AND_THIRD_PARTY_INVENTORY",
            "CORRESPONDING_SOURCE_AND_NOTICE",
        }
    }
    entries = evidence.get("records")
    if (
        evidence.get("schema_version") != 1
        or evidence.get("status") != "PASS"
        or evidence.get("source_lock_sha256") != lock_digest
        or evidence.get("verified_source_count") != len(expected)
        or not isinstance(entries, list)
        or len(entries) != len(expected)
    ):
        raise ValueError("Corresponding-source evidence does not match the current source lock")
    seen: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("Corresponding-source evidence contains a malformed record")
        record_id = entry.get("record_id")
        locked = expected.get(record_id)
        filename = entry.get("filename")
        if (
            locked is None
            or not isinstance(record_id, str)
            or record_id in seen
            or not isinstance(filename, str)
            or PurePosixPath(filename).name != filename
            or filename in {"", ".", ".."}
            or entry.get("expected_sha256") != locked["sha256"]
            or entry.get("observed_sha256") != locked["sha256"]
            or not isinstance(entry.get("byte_length"), int)
            or entry["byte_length"] <= 0
            or entry.get("status") != "PASS"
        ):
            raise ValueError("Corresponding-source record differs from the current source lock")
        seen.add(record_id)
    if seen != set(expected):
        raise ValueError("Corresponding-source evidence omits a locked source package")
    return evidence


def expected_source_revisions(source_lock_path: Path) -> dict[str, str]:
    records = {row["id"]: row for row in load_source_lock(source_lock_path)["records"]}
    return {
        "ocp": records["ocp-source-7.9.3.1.1"]["revision"],
        "pywrap": records["ocp-pywrap-source-9251940"]["revision"],
        "occt": records["occt-source-7.9.3"]["revision"],
    }


def expected_contract_digests(
    source_lock: Path, conda_lock: Path, contract: Path
) -> dict[str, str]:
    return {
        "source_lock_sha256": sha256(source_lock),
        "build_environment_lock_sha256": sha256(conda_lock),
        "build_contract_sha256": sha256(contract),
        "builder_sha256": sha256(BUILDER),
        "bundle_validator_sha256": sha256(Path(__file__)),
        "ocp_manifest_validator_sha256": sha256(MANIFEST_VALIDATOR),
        "source_lock_validator_sha256": sha256(SOURCE_LOCK_VALIDATOR),
        "source_fetcher_sha256": sha256(SOURCE_FETCHER),
    }


def seal_bundle(args: argparse.Namespace) -> dict[str, Any]:
    contract = read_json(args.build_contract, "Controlled-runtime build contract")
    if (
        contract.get("schema_version") != 1
        or contract.get("ocp_bindgen_workers") != 4
        or contract.get("cmake_parallel") != 4
    ):
        raise ValueError("Unsupported controlled-runtime build contract schema")
    manifest = load_and_validate_manifest(args.manifest, args.source_lock)
    evidence = validate_source_evidence(args.source_evidence, args.source_lock)
    if manifest.get("input_lock_sha256") != sha256(args.source_lock):
        raise ValueError("The OCP manifest is not bound to the current source lock")
    toolchain = manifest.get("toolchain", {})
    if (
        toolchain.get("ocp_bindgen_workers") != contract.get("ocp_bindgen_workers")
        or toolchain.get("cmake_parallel") != contract.get("cmake_parallel")
        or toolchain.get("windows_sdk") != contract.get("windows_sdk_version")
        or toolchain.get("cmake_generator") != contract.get("cmake_generator")
        or toolchain.get("python") != contract.get("target", {}).get("python_version")
        or toolchain.get("cmake") != contract.get("toolchain", {}).get("cmake")
        or toolchain.get("compiler") != contract.get("toolchain", {}).get("compiler")
    ):
        raise ValueError("The built runtime toolchain differs from the checked-in contract")
    if not str(toolchain.get("python", "")).startswith(
        str(contract["target"]["python_minor"]) + "."
    ):
        raise ValueError("The controlled runtime Python version differs from the target contract")
    if {
        "ocp": manifest.get("ocp_source_revision"),
        "pywrap": manifest.get("ocp_pywrap_source_revision"),
        "occt": manifest.get("occt_source_revision"),
    } != expected_source_revisions(args.source_lock):
        raise ValueError(
            "The controlled runtime source revisions differ from the exact source lock"
        )
    timings = manifest.get("build_timings")
    required_phases = {
        "occt_native_build": contract.get("cmake_parallel"),
        "pywrap_generation": contract.get("ocp_bindgen_workers"),
        "ocp_native_compile_link": contract.get("cmake_parallel"),
    }
    if not isinstance(timings, list):
        raise ValueError("The controlled runtime is missing build timing evidence")
    for phase, worker_count in required_phases.items():
        matches = [
            entry for entry in timings if isinstance(entry, dict) and entry.get("phase") == phase
        ]
        if (
            len(matches) != 1
            or matches[0].get("worker_count") != worker_count
            or not isinstance(matches[0].get("duration_seconds"), (int, float))
            or matches[0]["duration_seconds"] < 0
            or not matches[0].get("started_utc")
            or not matches[0].get("ended_utc")
        ):
            raise ValueError(f"Controlled runtime timing evidence is invalid for {phase}")
        try:
            started = datetime.fromisoformat(matches[0]["started_utc"])
            ended = datetime.fromisoformat(matches[0]["ended_utc"])
        except (TypeError, ValueError) as error:
            raise ValueError(f"Controlled runtime timestamps are invalid for {phase}") from error
        if ended < started:
            raise ValueError(f"Controlled runtime timing order is invalid for {phase}")
    source_package = args.site_packages / "OCP"
    if not source_package.is_dir():
        raise ValueError("The controlled OCP package is missing from the build environment")

    shutil.rmtree(args.bundle, ignore_errors=True)
    args.bundle.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_package, args.bundle / "OCP", symlinks=True)
    shutil.copy2(args.manifest, args.bundle / MANIFEST_NAME)
    shutil.copy2(args.source_evidence, args.bundle / SOURCE_EVIDENCE_NAME)
    runtime_files = runtime_inventory(args.bundle / "OCP")
    inventory_files = runtime_files + [
        {
            "relative_path": MANIFEST_NAME,
            "sha256": sha256(args.bundle / MANIFEST_NAME),
            "byte_length": (args.bundle / MANIFEST_NAME).stat().st_size,
        },
        {
            "relative_path": SOURCE_EVIDENCE_NAME,
            "sha256": sha256(args.bundle / SOURCE_EVIDENCE_NAME),
            "byte_length": (args.bundle / SOURCE_EVIDENCE_NAME).stat().st_size,
        },
    ]
    digests = expected_contract_digests(args.source_lock, args.conda_lock, args.build_contract)
    metadata = {
        "schema_version": BUNDLE_SCHEMA_VERSION,
        "status": "SEALED",
        "cache_key": args.cache_key,
        **digests,
        "source_revisions": {
            "ocp": manifest["ocp_source_revision"],
            "pywrap": manifest["ocp_pywrap_source_revision"],
            "occt": manifest["occt_source_revision"],
        },
        "target": contract["target"],
        "toolchain": toolchain,
        "ocp_bindgen_workers": contract["ocp_bindgen_workers"],
        "cmake_parallel": contract["cmake_parallel"],
        "runtime_file_count": len(runtime_files),
        "runtime_files": runtime_files,
        "bundle_content_sha256": canonical_digest(inventory_files),
        "controlled_manifest_sha256": sha256(args.bundle / MANIFEST_NAME),
        "source_evidence_sha256": sha256(args.bundle / SOURCE_EVIDENCE_NAME),
        "source_evidence_count": evidence["verified_source_count"],
        "build_timings": manifest.get("build_timings", []),
    }
    metadata_path = args.bundle / METADATA_NAME
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    validate_bundle(
        args.bundle,
        args.source_lock,
        args.conda_lock,
        args.build_contract,
        args.cache_key,
    )
    return metadata


def validate_bundle(
    bundle: Path,
    source_lock: Path,
    conda_lock: Path,
    build_contract: Path,
    cache_key: str,
) -> dict[str, Any]:
    if not bundle.is_dir() or bundle.is_symlink():
        raise ValueError("The controlled runtime bundle directory is missing or unsafe")
    metadata_path = bundle / METADATA_NAME
    manifest_path = bundle / MANIFEST_NAME
    evidence_path = bundle / SOURCE_EVIDENCE_NAME
    metadata = read_json(metadata_path, "Controlled-runtime metadata")
    manifest = load_and_validate_manifest(manifest_path, source_lock)
    evidence = validate_source_evidence(evidence_path, source_lock)
    reject_runner_paths([manifest_path, evidence_path, metadata_path])
    contract = read_json(build_contract, "Controlled-runtime build contract")
    expected_digests = expected_contract_digests(source_lock, conda_lock, build_contract)
    if (
        metadata.get("schema_version") != BUNDLE_SCHEMA_VERSION
        or metadata.get("status") != "SEALED"
        or metadata.get("cache_key") != cache_key
        or metadata.get("target") != contract.get("target")
        or contract.get("schema_version") != 1
        or contract.get("ocp_bindgen_workers") != 4
        or contract.get("cmake_parallel") != 4
        or metadata.get("ocp_bindgen_workers") != 4
        or metadata.get("cmake_parallel") != 4
    ):
        raise ValueError(
            "Controlled-runtime cache metadata does not match the current build contract"
        )
    for name, digest in expected_digests.items():
        if metadata.get(name) != digest:
            raise ValueError(f"Controlled-runtime cache metadata mismatch: {name}")
    toolchain = metadata.get("toolchain")
    if (
        not isinstance(toolchain, dict)
        or toolchain != manifest.get("toolchain")
        or toolchain.get("ocp_bindgen_workers") != 4
        or toolchain.get("cmake_parallel") != 4
        or toolchain.get("windows_sdk") != contract.get("windows_sdk_version")
        or toolchain.get("cmake_generator") != contract.get("cmake_generator")
        or toolchain.get("python") != contract.get("target", {}).get("python_version")
        or toolchain.get("cmake") != contract.get("toolchain", {}).get("cmake")
        or toolchain.get("compiler") != contract.get("toolchain", {}).get("compiler")
    ):
        raise ValueError("Controlled-runtime toolchain metadata differs from the build contract")
    if (
        metadata.get("source_revisions") != expected_source_revisions(source_lock)
        or metadata.get("source_revisions")
        != {
            "ocp": manifest.get("ocp_source_revision"),
            "pywrap": manifest.get("ocp_pywrap_source_revision"),
            "occt": manifest.get("occt_source_revision"),
        }
        or not str(toolchain.get("python", "")).startswith(
            str(contract["target"]["python_minor"]) + "."
        )
    ):
        raise ValueError("Controlled-runtime source revisions differ from the manifest")
    runtime_files = runtime_inventory(bundle / "OCP")
    if runtime_files != metadata.get("runtime_files"):
        raise ValueError("A controlled-runtime file hash, size, or inventory differs from metadata")
    reject_runner_paths([path for path in (bundle / "OCP").rglob("*.py") if path.is_file()])
    if metadata.get("runtime_file_count") != len(runtime_files):
        raise ValueError("Controlled-runtime metadata file count is incorrect")
    expected_bundle_paths = {
        f"OCP/{entry['relative_path'].removeprefix('OCP/')}" for entry in runtime_files
    } | {METADATA_NAME, MANIFEST_NAME, SOURCE_EVIDENCE_NAME}
    actual_bundle_paths: set[str] = set()
    actual_bundle_dirs: set[str] = set()
    for path in bundle.rglob("*"):
        if path.is_symlink():
            raise ValueError("The controlled runtime bundle cannot contain symbolic links")
        if path.is_file():
            actual_bundle_paths.add(path.relative_to(bundle).as_posix())
        elif path.is_dir():
            actual_bundle_dirs.add(path.relative_to(bundle).as_posix())
    expected_bundle_dirs = {"OCP"}
    for entry in runtime_files:
        parent = PurePosixPath(entry["relative_path"]).parent
        while parent.as_posix() != ".":
            expected_bundle_dirs.add(parent.as_posix())
            parent = parent.parent
    if actual_bundle_paths != expected_bundle_paths:
        raise ValueError("The controlled runtime bundle contains missing or unexpected files")
    if actual_bundle_dirs != expected_bundle_dirs:
        raise ValueError("The controlled runtime bundle contains missing or unexpected directories")
    inventory_files = runtime_files + [
        {
            "relative_path": MANIFEST_NAME,
            "sha256": sha256(manifest_path),
            "byte_length": manifest_path.stat().st_size,
        },
        {
            "relative_path": SOURCE_EVIDENCE_NAME,
            "sha256": sha256(evidence_path),
            "byte_length": evidence_path.stat().st_size,
        },
    ]
    if metadata.get("bundle_content_sha256") != canonical_digest(inventory_files):
        raise ValueError("Controlled-runtime bundle content digest does not match")
    if metadata.get("controlled_manifest_sha256") != sha256(manifest_path):
        raise ValueError("Controlled-runtime manifest digest does not match metadata")
    if metadata.get("source_evidence_sha256") != sha256(evidence_path):
        raise ValueError("Controlled-runtime source-evidence digest does not match metadata")
    if metadata.get("source_evidence_count") != evidence.get("verified_source_count"):
        raise ValueError("Controlled-runtime source-evidence count does not match metadata")
    validate_staged_tree(bundle, manifest)
    return metadata


def install_bundle(args: argparse.Namespace) -> None:
    validate_bundle(
        args.bundle,
        args.source_lock,
        args.conda_lock,
        args.build_contract,
        args.cache_key,
    )
    opaque_libraries = args.site_packages / "cadquery_ocp_novtk.libs"
    opaque_package = args.site_packages / "cadquery_ocp_novtk"
    target = args.site_packages / "OCP"
    shutil.rmtree(target, ignore_errors=True)
    shutil.rmtree(opaque_libraries, ignore_errors=True)
    shutil.rmtree(opaque_package, ignore_errors=True)
    shutil.copytree(args.bundle / "OCP", target)
    if opaque_libraries.exists() or opaque_package.exists():
        raise ValueError("An opaque cadquery_ocp_novtk runtime survived controlled installation")
    print("CONTROLLED_OCP_INSTALL_PASS opaque_wheel_libraries=absent", flush=True)


def smoke_test() -> None:
    from OCP.BRepCheck import BRepCheck_Analyzer
    from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox

    shape = BRepPrimAPI_MakeBox(10.0, 20.0, 30.0).Shape()
    if not BRepCheck_Analyzer(shape).IsValid():
        raise ValueError("The controlled OCP CAD smoke produced an invalid box")
    print("CONTROLLED_OCP_SMOKE_PASS import=OCP CAD=valid-box", flush=True)


def add_bundle_inputs(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument(
        "--source-lock", type=Path, default=Path("tools/packaging/windows_native_source_lock.json")
    )
    parser.add_argument(
        "--conda-lock", type=Path, default=Path("tools/packaging/packlab-ocp-bindings-win.lock")
    )
    parser.add_argument(
        "--build-contract",
        type=Path,
        default=Path("tools/packaging/controlled_ocp_runtime_contract.json"),
    )
    parser.add_argument("--cache-key", required=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    seal_parser = subparsers.add_parser("seal")
    seal_parser.add_argument("--site-packages", type=Path, required=True)
    seal_parser.add_argument("--manifest", type=Path, required=True)
    seal_parser.add_argument("--source-evidence", type=Path, required=True)
    seal_parser.add_argument("--bundle", type=Path, required=True)
    seal_parser.add_argument(
        "--source-lock", type=Path, default=Path("tools/packaging/windows_native_source_lock.json")
    )
    seal_parser.add_argument(
        "--conda-lock", type=Path, default=Path("tools/packaging/packlab-ocp-bindings-win.lock")
    )
    seal_parser.add_argument(
        "--build-contract",
        type=Path,
        default=Path("tools/packaging/controlled_ocp_runtime_contract.json"),
    )
    seal_parser.add_argument("--cache-key", required=True)
    validate_parser = subparsers.add_parser("validate")
    add_bundle_inputs(validate_parser)
    install_parser = subparsers.add_parser("install")
    add_bundle_inputs(install_parser)
    install_parser.add_argument("--site-packages", type=Path, required=True)
    subparsers.add_parser("smoke")
    args = parser.parse_args()
    if args.command == "seal":
        metadata = seal_bundle(args)
        print(
            "CONTROLLED_OCP_BUNDLE_SEALED "
            f"files={metadata['runtime_file_count']} "
            f"content_sha256={metadata['bundle_content_sha256']} "
            f"manifest_sha256={metadata['controlled_manifest_sha256']} "
            f"source_lock_sha256={metadata['source_lock_sha256']}",
            flush=True,
        )
    elif args.command == "validate":
        metadata = validate_bundle(
            args.bundle,
            args.source_lock,
            args.conda_lock,
            args.build_contract,
            args.cache_key,
        )
        print(
            "CONTROLLED_OCP_BUNDLE_VALID "
            f"files={metadata['runtime_file_count']} "
            f"content_sha256={metadata['bundle_content_sha256']} "
            f"manifest_sha256={metadata['controlled_manifest_sha256']}",
            flush=True,
        )
    elif args.command == "install":
        install_bundle(args)
    else:
        smoke_test()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
