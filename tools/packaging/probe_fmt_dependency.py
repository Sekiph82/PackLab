"""Probe locked Windows fmt package provenance and native import ownership."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tarfile
import urllib.request
from pathlib import Path, PurePosixPath
from typing import Any

from tools.packaging.windows_native_runtime_policy import deployment_role

CONTRACT = Path("tools/packaging/fmt_dependency_contract.json")
CONDA_LOCK = Path("tools/packaging/packlab-ocp-bindings-win.lock")
SOURCE_LOCK = Path("tools/packaging/windows_native_source_lock.json")
FMT_DLL_NAME = "fmt.dll"
RECIPE_URL_TEMPLATE = "https://raw.githubusercontent.com/{repository}/{commit}/{path}"
ANACONDA_API = "https://api.anaconda.org/package/conda-forge/fmt"


def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def digest_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def fetch(url: str, timeout: int = 90) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "PackLab-PL0350-fmt-probe/1"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def package_lock_entry(lock_path: Path) -> dict[str, Any]:
    rows = [row for row in package_lock_rows(lock_path).values() if row.get("name") == "fmt"]
    if len(rows) != 1:
        raise ValueError("the Windows OCP lock must contain one fmt package record")
    return rows[0]


def package_lock_rows(lock_path: Path) -> dict[str, dict[str, Any]]:
    content = lock_path.read_text(encoding="utf-8")
    starts = list(re.finditer(r"(?m)^- name: ([^\r\n]+)$", content))
    rows: dict[str, dict[str, Any]] = {}

    def field(block: str, pattern: str, package_name: str) -> str:
        match = re.search(pattern, block)
        if match is None:
            raise ValueError(f"conda package lock record is incomplete: {package_name}")
        return match.group(1)

    for index, start in enumerate(starts):
        end = starts[index + 1].start() if index + 1 < len(starts) else len(content)
        block = content[start.start() : end]
        name = start.group(1).strip()
        version = field(block, r"(?m)^  version: ([^\r\n]+)$", name).strip("'\"")
        platform = field(block, r"(?m)^  platform: ([^\r\n]+)$", name)
        url = field(block, r"(?m)^  url: (https://[^\s]+)$", name)
        digest = field(block, r"(?m)^    sha256: ([0-9a-f]{64})$", name)
        artifact = url.rsplit("/", 1)[-1]
        prefix = f"{name}-{version}-"
        suffix = ".conda" if artifact.endswith(".conda") else ".tar.bz2"
        if not artifact.startswith(prefix) or not artifact.endswith(suffix):
            raise ValueError(f"conda package lock filename has no exact build identity: {name}")
        build = artifact[len(prefix) : -len(suffix)]
        if platform != "win-64":
            raise ValueError(f"native conda lock has a non-Windows package record: {name}")
        rows[name.casefold()] = {
            "name": name,
            "version": version,
            "build": build,
            "platform": platform,
            "url": url,
            "hash": {"sha256": digest},
        }
    if not rows:
        raise ValueError("exact Windows native conda lock is empty")
    return rows


def verify_pinned_identity(contract: dict[str, Any], lock_path: Path) -> dict[str, Any]:
    package = contract["package"]
    row = package_lock_entry(lock_path)
    lock_digest = row.get("hash", {}).get("sha256")
    if (
        row.get("version") != package["version"]
        or row.get("build") != package["build"]
        or row.get("url") != package["url"]
        or lock_digest != package["sha256"]
        or row.get("name") != package["name"]
    ):
        raise ValueError("fmt dependency contract differs from the exact Windows conda lock")
    return row


def verify_source_and_recipe(contract: dict[str, Any], scratch: Path) -> dict[str, Any]:
    source = contract["upstream_source"]
    archive = fetch(source["url"])
    source_digest = digest_bytes(archive)
    if source_digest != source["sha256"]:
        raise ValueError(
            "fmt upstream source archive SHA-256 differs from its pinned source record"
        )
    with tarfile.open(fileobj=__import__("io").BytesIO(archive), mode="r:gz") as tar:
        member = tar.getmember(source["license_path"])
        if not member.isfile():
            raise ValueError("fmt source archive license entry is not a regular file")
        stream = tar.extractfile(member)
        if stream is None:
            raise ValueError("fmt source archive license could not be read")
        license_bytes = stream.read()
    if digest_bytes(license_bytes) != source["license_sha256"]:
        raise ValueError("fmt MIT license bytes differ from the pinned notice digest")
    recipe = contract["conda_forge_recipe"]
    recipe_url = RECIPE_URL_TEMPLATE.format(**recipe)
    recipe_bytes = fetch(recipe_url)
    if digest_bytes(recipe_bytes) != recipe["sha256"]:
        raise ValueError("pinned conda-forge fmt recipe bytes differ from contract")
    recipe_text = recipe_bytes.decode("utf-8")
    required = (
        'set version = "12.1.0"',
        "ea7de4299689e12b6dddd392f9896f08fb0777ac7168897a244a6d6085043fea",
        "license: MIT",
        "license_file: LICENSE",
    )
    if any(fragment not in recipe_text for fragment in required):
        raise ValueError("pinned conda-forge recipe does not prove the locked fmt source/license")
    scratch.mkdir(parents=True, exist_ok=True)
    (scratch / "fmt-source-12.1.0.tar.gz").write_bytes(archive)
    (scratch / "fmt-recipe-meta.yaml").write_bytes(recipe_bytes)
    return {
        "source_sha256": source_digest,
        "source_bytes": len(archive),
        "license_sha256": digest_bytes(license_bytes),
        "license_bytes": len(license_bytes),
        "recipe_sha256": digest_bytes(recipe_bytes),
        "recipe_url": recipe_url,
    }


def verify_anaconda_metadata(contract: dict[str, Any], scratch: Path) -> dict[str, Any]:
    package = contract["package"]
    metadata = json.loads(fetch(ANACONDA_API))
    matches = [
        row
        for row in metadata["files"]
        if row.get("basename")
        == f"{package['subdir']}/fmt-{package['version']}-{package['build']}.conda"
    ]
    if len(matches) != 1:
        raise ValueError("Anaconda package metadata did not return exactly one locked fmt build")
    row = matches[0]
    attrs = row.get("attrs", {})
    if (
        row.get("sha256") != package["sha256"]
        or row.get("size") != package["byte_length"]
        or row.get("version") != package["version"]
        or attrs.get("build") != package["build"]
        or attrs.get("subdir") != package["subdir"]
        or attrs.get("license") != contract["conda_forge_recipe"]["package_license"]
    ):
        raise ValueError("Anaconda published package metadata differs from the locked fmt identity")
    package_archive = fetch(package["url"])
    archive_sha256 = digest_bytes(package_archive)
    if archive_sha256 != package["sha256"] or len(package_archive) != package["byte_length"]:
        raise ValueError(
            "downloaded fmt conda archive differs from the exact locked digest and size"
        )
    scratch.mkdir(parents=True, exist_ok=True)
    (scratch / f"fmt-{package['version']}-{package['build']}.conda").write_bytes(package_archive)
    return {
        "full_name": row["full_name"],
        "sha256": row["sha256"],
        "byte_length": row["size"],
        "downloaded_archive_sha256": archive_sha256,
        "downloaded_archive_bytes": len(package_archive),
        "license": attrs["license"],
        "license_family": attrs.get("license_family"),
        "dependencies": attrs.get("depends", []),
    }


def load_conda_owners(prefix: Path) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    owners: dict[str, dict[str, Any]] = {}
    records: dict[str, dict[str, Any]] = {}
    for record_path in sorted((prefix / "conda-meta").glob("*.json")):
        record = json.loads(record_path.read_text(encoding="utf-8"))
        name = record.get("name")
        if not isinstance(name, str):
            continue
        records[name.casefold()] = record
        paths_data = record.get("paths_data", {}).get("paths", [])
        hashes = {
            str(entry.get("_path", "")).replace("\\", "/").casefold(): entry.get("sha256")
            for entry in paths_data
        }
        for relative in record.get("files", []):
            key = str(relative).replace("\\", "/").casefold()
            owners[key] = {"record": record, "sha256": hashes.get(key)}
    return owners, records


def _import_names(path: Path) -> list[str]:
    import pefile

    image = pefile.PE(str(path), fast_load=False)
    try:
        if image.FILE_HEADER.Machine != pefile.MACHINE_TYPE["IMAGE_FILE_MACHINE_AMD64"]:
            raise ValueError(f"native dependency is not x64 PE: {path.name}")
        names: set[str] = set()
        for attribute in ("DIRECTORY_ENTRY_IMPORT", "DIRECTORY_ENTRY_DELAY_IMPORT"):
            for item in getattr(image, attribute, []):
                raw = item.dll
                names.add(raw.decode("ascii").casefold())
        return sorted(names)
    finally:
        image.close()


def _find_dll(name: str, search_dirs: list[Path]) -> Path | None:
    for directory in search_dirs:
        if not directory.is_dir():
            continue
        matches = [
            path for path in directory.iterdir() if path.is_file() and path.name.casefold() == name
        ]
        if len(matches) > 1:
            raise ValueError(f"ambiguous native DLL resolution for {name} in {directory}")
        if matches:
            return matches[0]
    return None


def _locked_conda_package(
    record: dict[str, Any], lock_rows: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    name = str(record.get("name", "")).casefold()
    locked = lock_rows.get(name)
    if locked is None:
        raise ValueError(f"native transitive package is absent from the explicit lock: {name}")
    url = str(record.get("url", ""))
    sha = record.get("sha256") or record.get("repodata_record", {}).get("sha256")
    observed = {
        "version": record.get("version"),
        "build": record.get("build"),
        "url": url,
        "sha256": sha,
    }
    expected = {
        "version": locked.get("version"),
        "build": locked.get("build"),
        "url": locked.get("url"),
        "sha256": locked.get("hash", {}).get("sha256"),
    }
    mismatches = [
        key
        for key, value in expected.items()
        if (observed[key] is not None if key == "sha256" else True) and observed[key] != value
    ]
    if mismatches:
        raise ValueError(
            f"installed native dependency differs from exact lock: {name}; "
            f"mismatched_fields={','.join(mismatches)}; observed={json.dumps(observed, sort_keys=True)}"
        )
    return {
        "name": name,
        "version": record.get("version"),
        "build": record.get("build"),
        "url": url,
        "sha256": locked.get("hash", {}).get("sha256"),
        "installed_record_sha256": sha,
    }


def inspect_import_closure(
    dll_path: Path,
    prefix: Path,
    lock_rows: dict[str, dict[str, Any]],
    source_records: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    system_root = Path(os.environ.get("SystemRoot", r"C:\Windows"))
    system_dirs = [system_root / "System32", system_root / "SysWOW64"]
    search_dirs = [dll_path.parent, prefix / "Library/bin", prefix / "Scripts", *system_dirs]
    owners, _ = load_conda_owners(prefix)
    root_relative = dll_path.relative_to(prefix).as_posix().casefold()
    root_owner = owners.get(root_relative)
    if root_owner is None:
        raise ValueError("fmt.dll is missing its exact conda package file owner")
    root_record = root_owner["record"]
    root_package = _locked_conda_package(root_record, lock_rows)
    root_source = [
        row
        for row in source_records.values()
        if row.get("binary_package", {}).get("name", "").casefold() == root_package["name"]
        and row.get("binary_package", {}).get("sha256") == root_package["sha256"]
    ]
    root_hash = digest_file(dll_path)
    if root_owner.get("sha256") != root_hash:
        raise ValueError("fmt.dll bytes differ from the exact conda package file manifest")
    closure: list[dict[str, Any]] = [
        {
            "name": dll_path.name.casefold(),
            "path": root_relative,
            "package": root_package,
            "source_record_id": root_source[0]["id"] if len(root_source) == 1 else None,
            "owner": "fmt package" if len(root_source) == 1 else "SOURCE_OR_LICENSE_UNRESOLVED",
            "sha256": root_hash,
            "status": "PASS" if len(root_source) == 1 else "BLOCKED",
        }
    ]
    pending = [(name, dll_path) for name in _import_names(dll_path)]
    seen: set[str] = set()
    while pending:
        name, parent = pending.pop()
        if name in seen:
            continue
        seen.add(name)
        resolved = _find_dll(name, search_dirs)
        if resolved is None:
            api_set = name.startswith(("api-ms-win-", "ext-ms-win-"))
            item = {
                "name": name,
                "parent": parent.name,
                "owner": "WINDOWS_API_SET_UNRESOLVED" if api_set else "UNKNOWN",
                "status": "BLOCKED",
            }
            if api_set:
                item["deployment_role"] = "WINDOWS_OS_COMPONENT"
            closure.append(item)
            continue
        if any(resolved.is_relative_to(directory) for directory in system_dirs):
            closure.append(
                {
                    "name": name,
                    "path": resolved.relative_to(system_root).as_posix(),
                    "owner": "Windows system",
                    "sha256": digest_file(resolved),
                    "status": "PASS",
                }
            )
            continue
        relative = resolved.relative_to(prefix).as_posix().casefold()
        owner_info = owners.get(relative)
        if owner_info is None:
            closure.append(
                {"name": name, "path": relative, "owner": "UNKNOWN_PACKAGE", "status": "BLOCKED"}
            )
            continue
        record = owner_info["record"]
        locked_package = _locked_conda_package(record, lock_rows)
        file_hash = digest_file(resolved)
        if not owner_info.get("sha256") or owner_info["sha256"] != file_hash:
            raise ValueError(f"installed native DLL differs from conda file manifest: {relative}")
        source_matches = [
            row
            for row in source_records.values()
            if row.get("binary_package", {}).get("name", "").casefold() == locked_package["name"]
            and row.get("binary_package", {}).get("sha256") == locked_package["sha256"]
        ]
        # These conda packages exist only to make the hosted compiler environment
        # complete. They are not PackLab runtime payloads: UCRT is serviced by
        # Windows 10/11 and the VC runtime is a separately detected prerequisite.
        role = deployment_role(locked_package["name"])
        if role is not None:
            closure.append(
                {
                    "name": name,
                    "path": relative,
                    "package": locked_package,
                    "owner": role,
                    "deployment_role": role,
                    "sha256": file_hash,
                    "status": "PASS",
                }
            )
            continue
        if len(source_matches) != 1:
            closure.append(
                {
                    "name": name,
                    "path": relative,
                    "package": locked_package,
                    "owner": "SOURCE_OR_LICENSE_UNRESOLVED",
                    "sha256": file_hash,
                    "status": "BLOCKED",
                }
            )
            continue
        closure.append(
            {
                "name": name,
                "path": relative,
                "package": locked_package,
                "source_record_id": source_matches[0]["id"],
                "sha256": file_hash,
                "status": "PASS",
            }
        )
        pending.extend((imported, resolved) for imported in _import_names(resolved))
    return sorted(closure, key=lambda row: row["name"])


def run_probe(prefix: Path, scratch: Path, generated_cmake: Path | None = None) -> dict[str, Any]:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if contract.get("pe_machine") != "IMAGE_FILE_MACHINE_AMD64":
        raise ValueError("fmt PE architecture contract is not locked to x86_64")
    row = verify_pinned_identity(contract, CONDA_LOCK)
    source_lock = json.loads(SOURCE_LOCK.read_text(encoding="utf-8"))
    source_records = {item["id"]: item for item in source_lock["records"]}
    fmt_source = source_records.get(contract["dependency_id"])
    if (
        fmt_source is None
        or fmt_source["sha256"] != contract["upstream_source"]["sha256"]
        or fmt_source["license_identifier"] != "MIT"
        or fmt_source.get("license_notice_sha256") != contract["upstream_source"]["license_sha256"]
    ):
        raise ValueError(
            "fmt source/notice contract is absent from the canonical native source lock"
        )
    source = verify_source_and_recipe(contract, scratch)
    published = verify_anaconda_metadata(contract, scratch)
    if generated_cmake is not None:
        cmake_text = generated_cmake.read_text(encoding="utf-8")
        if "fmt::fmt" not in cmake_text:
            raise ValueError("generated OCP CMake target no longer links the exact fmt::fmt target")
    config_candidates = list((prefix / "Library").rglob("fmt-config.cmake"))
    target_candidates = [
        path for path in (prefix / "Library").rglob("fmt-targets*.cmake") if path.is_file()
    ]
    target_text = "\n".join(path.read_text(encoding="utf-8") for path in target_candidates)
    if (
        len(config_candidates) != 1
        or not target_candidates
        or FMT_DLL_NAME not in target_text.casefold()
    ):
        raise ValueError("locked fmt CMake package does not resolve its shared imported DLL target")
    archive_url = contract["package"]["url"]
    archive_path = scratch / "fmt-12.1.0-h1ced75a_1.conda"
    archive_path.write_bytes(fetch(archive_url))
    if (
        archive_path.stat().st_size != contract["package"]["byte_length"]
        or digest_file(archive_path) != contract["package"]["sha256"]
    ):
        raise ValueError(
            "exact locked conda fmt package archive failed SHA-256 or byte-length validation"
        )

    package_record_path = prefix / "conda-meta" / "fmt-12.1.0-h1ced75a_1.json"
    if not package_record_path.is_file():
        raise ValueError("exact fmt package is not installed in the locked hosted environment")
    package_record = json.loads(package_record_path.read_text(encoding="utf-8"))
    installed = _locked_conda_package(package_record, {"fmt": row})
    dll = prefix / PurePosixPath(contract["package"]["dll_relative_path"])
    if not dll.is_file():
        raise ValueError("locked conda fmt package does not provide Library/bin/fmt.dll")
    owners, _ = load_conda_owners(prefix)
    owner = owners.get(contract["package"]["dll_relative_path"].casefold())
    dll_sha = digest_file(dll)
    if not owner or owner.get("sha256") != dll_sha:
        raise ValueError("installed fmt.dll hash does not match its conda package file manifest")
    closure = inspect_import_closure(dll, prefix, package_lock_rows(CONDA_LOCK), source_records)
    blocked = [item for item in closure if item.get("status") != "PASS"]
    return {
        "schema_version": 1,
        "status": "BLOCKED" if blocked else "PASS",
        "reason": "UNKNOWN_NATIVE_IMPORT_OWNERS" if blocked else None,
        "package_lock": {
            "name": contract["package"]["name"],
            "version": contract["package"]["version"],
            "build": contract["package"]["build"],
            "sha256": contract["package"]["sha256"],
            "byte_length": contract["package"]["byte_length"],
            "installed": installed,
            "dll_path": contract["package"]["dll_relative_path"],
            "dll_sha256": dll_sha,
            "pe_machine": "IMAGE_FILE_MACHINE_AMD64",
        },
        "upstream_source_and_notice": source,
        "anaconda_published_metadata": published,
        "generated_ocp_link_target": "fmt::fmt" if generated_cmake is not None else "NOT_CHECKED",
        "fmt_cmake_config": [path.relative_to(prefix).as_posix() for path in config_candidates],
        "fmt_cmake_target_files": [
            path.relative_to(prefix).as_posix() for path in target_candidates
        ],
        "native_import_closure": closure,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prefix", type=Path, default=Path(sys.prefix))
    parser.add_argument("--scratch", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--generated-cmake", type=Path)
    parser.add_argument("--assert-pass", action="store_true")
    args = parser.parse_args()
    report: dict[str, Any]
    try:
        report = run_probe(args.prefix.resolve(), args.scratch, args.generated_cmake)
    except Exception as error:
        report = {
            "schema_version": 1,
            "status": "BLOCKED",
            "reason": "PROBE_ERROR",
            "error": str(error),
        }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"FMT_DEPENDENCY_PROBE_{report['status']} reason={report.get('reason') or 'NONE'}")
    if args.assert_pass and report["status"] != "PASS":
        raise SystemExit(1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
