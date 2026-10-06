"""Create path-free compliance evidence for the exact frozen Windows Studio tree."""

from __future__ import annotations

import argparse
import ast
import ctypes
import hashlib
import importlib.metadata
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

SCHEMA_VERSION = 1
PE_SUFFIXES = {".dll", ".exe", ".pyd"}
TEXT_LICENSE_SUFFIXES = {".txt", ".md", ".json", ".html"}
LICENSE_NAME = re.compile(r"(?:license|licence|copying|notice|copyright)", re.IGNORECASE)
BUILD_REVISION = re.compile(r"^[0-9a-f]{40}$")
SEMVER = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")


def canonical_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_posix_path(value: str) -> str | None:
    normalized = value.replace("\\", "/")
    windows_path = PureWindowsPath(normalized)
    posix_path = PurePosixPath(normalized)
    if windows_path.is_absolute() or windows_path.drive or posix_path.is_absolute():
        return None
    if any(part in {"", ".", ".."} for part in posix_path.parts):
        return None
    return posix_path.as_posix()


def read_toc(path: Path) -> list[tuple[str, str, str]]:
    """Read a PyInstaller pprint TOC using literal_eval, never its eval loader."""
    raw = ast.literal_eval(path.read_text(encoding="utf-8"))
    if isinstance(raw, tuple) and len(raw) == 1 and isinstance(raw[0], list):
        raw = raw[0]
    if not isinstance(raw, (tuple, list)):
        raise ValueError("PyInstaller TOC has an unexpected top-level shape")
    records: list[tuple[str, str, str]] = []
    for record in raw:
        if not isinstance(record, (tuple, list)) or len(record) < 3:
            continue
        destination, source, kind = record[:3]
        if isinstance(destination, str) and isinstance(source, str) and isinstance(kind, str):
            records.append((destination, source, kind))
    if not records:
        raise ValueError("PyInstaller TOC contains no file records")
    return records


def analysis_source_paths(path: Path) -> list[str]:
    """Extract analyzed source inputs for composite PYZ/PKG executable files."""
    raw = ast.literal_eval(path.read_text(encoding="utf-8"))
    if not isinstance(raw, (tuple, list)):
        raise ValueError("PyInstaller analysis TOC has an unexpected top-level shape")
    try:
        from PyInstaller.building.build_main import Analysis
    except ImportError as error:
        raise ValueError(
            "The locked PyInstaller environment is required to read its analysis TOC"
        ) from error
    guts = dict(zip((item[0] for item in Analysis._GUTS), raw, strict=True))
    sources: list[str] = []
    for key in ("scripts", "pure", "binaries", "zipfiles", "datas", "_modules_outside_pyz"):
        entries = guts.get(key, [])
        if not isinstance(entries, (tuple, list)):
            continue
        for entry in entries:
            if isinstance(entry, (tuple, list)) and len(entry) >= 2 and isinstance(entry[1], str):
                sources.append(entry[1])
    return sources


def norm_source(path: Path | str) -> str:
    return os.path.normcase(os.path.realpath(os.fspath(path)))


def is_python_runtime_source(path: Path, stdlib_root: str) -> bool:
    key = norm_source(path)
    if not key.startswith(stdlib_root + os.sep):
        return False
    return not any(part in {"site-packages", "dist-packages"} for part in Path(key).parts)


def is_windows_api_runtime(path: Path) -> bool:
    name = path.name.casefold()
    return name.startswith(("api-ms-win-", "ext-ms-win-", "vcruntime", "ucrtbase"))


def normalized_distribution_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def distribution_source_index(
    distributions: list[importlib.metadata.Distribution],
) -> tuple[
    dict[str, list[importlib.metadata.Distribution]], dict[str, importlib.metadata.Distribution]
]:
    owners: dict[str, list[importlib.metadata.Distribution]] = defaultdict(list)
    by_name: dict[str, importlib.metadata.Distribution] = {}
    for distribution in distributions:
        name = distribution.metadata.get("Name")
        if not name:
            continue
        by_name[normalized_distribution_name(name)] = distribution
        for package_path in distribution.files or ():
            located = Path(str(distribution.locate_file(package_path)))
            owners[norm_source(located)].append(distribution)
    return owners, by_name


def toc_destinations(
    rows: list[tuple[str, str, str]], contents_dir: str, stage_root: Path
) -> dict[str, tuple[str, str]]:
    result: dict[str, tuple[str, str]] = {}
    for destination, source, kind in rows:
        relative = safe_posix_path(destination)
        if relative is None:
            raise ValueError("PyInstaller TOC contains an unsafe destination path")
        candidates = [relative]
        if kind not in {"EXECUTABLE", "PKG"} and not relative.startswith(f"{contents_dir}/"):
            candidates.append(f"{contents_dir}/{relative}")
        present = [
            candidate
            for candidate in candidates
            if (stage_root / PurePosixPath(candidate)).is_file()
        ]
        if len(present) > 1:
            raise ValueError("PyInstaller TOC destination maps to multiple staged files")
        staged_path = present[0] if present else candidates[-1]
        if staged_path in result:
            raise ValueError("PyInstaller TOC contains duplicate staged destinations")
        result[staged_path] = (source, kind)
    return result


def read_pe_metadata(path: Path) -> dict[str, str] | None:
    if os.name != "nt" or path.suffix.lower() not in PE_SUFFIXES:
        return None
    try:
        version = ctypes.WinDLL("version", use_last_error=True)
        version.GetFileVersionInfoSizeW.argtypes = [ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_uint)]
        version.GetFileVersionInfoSizeW.restype = ctypes.c_uint
        version.GetFileVersionInfoW.argtypes = [
            ctypes.c_wchar_p,
            ctypes.c_uint,
            ctypes.c_uint,
            ctypes.c_void_p,
        ]
        version.GetFileVersionInfoW.restype = ctypes.c_bool
        version.VerQueryValueW.argtypes = [
            ctypes.c_void_p,
            ctypes.c_wchar_p,
            ctypes.POINTER(ctypes.c_void_p),
            ctypes.POINTER(ctypes.c_uint),
        ]
        version.VerQueryValueW.restype = ctypes.c_bool
        size = version.GetFileVersionInfoSizeW(str(path), None)
        if not size:
            return None
        buffer = ctypes.create_string_buffer(size)
        if not version.GetFileVersionInfoW(str(path), 0, size, buffer):
            return None
        pointer = ctypes.c_void_p()
        length = ctypes.c_uint()
        strings: dict[str, str] = {}
        language = 0x0409
        codepage = 1200
        if version.VerQueryValueW(
            buffer, "\\VarFileInfo\\Translation", ctypes.byref(pointer), ctypes.byref(length)
        ):
            translation = ctypes.cast(pointer, ctypes.POINTER(ctypes.c_ushort))
            language, codepage = translation[0], translation[1]
        for field in ("FileVersion", "ProductVersion", "OriginalFilename", "CompanyName"):
            key = f"\\StringFileInfo\\{language:04x}{codepage:04x}\\{field}"
            if (
                version.VerQueryValueW(buffer, key, ctypes.byref(pointer), ctypes.byref(length))
                and pointer.value
            ):
                value = ctypes.cast(pointer, ctypes.c_wchar_p).value
                if value:
                    strings[field] = value.strip()
        return strings or None
    except (AttributeError, OSError, ValueError):
        return None


def distribution_license_files(
    distribution: importlib.metadata.Distribution,
) -> list[tuple[str, Path]]:
    result: list[tuple[str, Path]] = []
    for package_path in distribution.files or ():
        relative = safe_posix_path(str(package_path))
        if relative is None:
            continue
        path = Path(str(distribution.locate_file(package_path)))
        if not path.is_file() or (
            path.suffix.lower() not in TEXT_LICENSE_SUFFIXES and not LICENSE_NAME.search(path.name)
        ):
            continue
        if LICENSE_NAME.search(path.name) or "third-party-licenses" in path.name.lower():
            result.append((relative, path))
    return sorted(result, key=lambda row: row[0].casefold())


def copy_text_evidence(source: Path, destination: Path) -> str:
    raw = source.read_bytes()
    if len(raw) > 8 * 1024 * 1024:
        raise ValueError("License evidence file exceeds the text evidence size limit")
    raw.decode("utf-8", errors="strict")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def category_for(relative: str, kind: str | None, source: Path | None) -> str:
    suffix = Path(relative).suffix.lower()
    if kind == "EXECUTABLE" or suffix == ".exe":
        return "windows_executable"
    if suffix == ".dll":
        return "windows_shared_library"
    if suffix == ".pyd":
        return "python_native_extension"
    if suffix in {".zip", ".pyz", ".pkg"} or kind == "PKG":
        return "python_or_pyinstaller_archive"
    if source is not None and source.suffix.lower() in {".py", ".pyc"}:
        return "python_application_or_library_archive_member"
    if relative == "schemas" or "/schemas/" in f"/{relative}/" or relative.startswith("schemas/"):
        return "packlab_schema_resource"
    if relative.startswith("THIRD_PARTY_LICENSES/") or relative == "THIRD_PARTY_NOTICES.txt":
        return "compliance_license_text"
    if suffix in {".json", ".xml", ".txt", ".qm", ".rcc"}:
        return "data_or_resource"
    return "other_staged_file"


def license_rows(
    owners: set[str],
    by_name: dict[str, importlib.metadata.Distribution],
    registry: dict[str, Any],
    output_root: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, str]], set[str]]:
    component_rows: list[dict[str, Any]] = []
    notice_rows: list[dict[str, str]] = []
    unresolved: set[str] = set()
    supplements = registry.get("supplemental_evidence", {})
    native_review = registry.get("native_review", {})
    for owner in sorted(owners):
        distribution = by_name.get(owner)
        supplemental_owner = registry.get("supplemental_evidence", {}).get(owner)
        if distribution is None:
            if owner == "cpython-runtime":
                license_path = Path(sys.base_prefix) / "LICENSE.txt"
                license_id = "PSF-2.0"
                version = sys.version.split()[0]
                files = [("LICENSE.txt", license_path)] if license_path.is_file() else []
                supplement = None
            elif owner == "pyinstaller-bootloader":
                distribution = by_name.get("pyinstaller")
                license_id = None
                version = None
                files = []
                supplement = None
            elif owner in native_review:
                rule = native_review[owner]
                unresolved.add(f"component:{owner}")
                component_rows.append(
                    {
                        "component_id": owner,
                        "version": None,
                        "license_identifier": rule.get("license_identifier"),
                        "license_status": "UNRESOLVED",
                        "unresolved_reason": rule.get("reason")
                        or "This exact native/system component requires a reviewed redistribution mapping.",
                        "notice_files": [],
                    }
                )
                continue
            elif supplemental_owner:
                metadata_name = owner
                version_match = re.search(r"\d+(?:\.\d+)+", owner)
                version = version_match.group(0) if version_match else None
                license_id = supplemental_owner.get("license_identifier")
                files = []
                supplement = supplemental_owner
            else:
                component_id = owner
                unresolved.add(f"component:{component_id}")
                component_rows.append(
                    {
                        "component_id": component_id,
                        "version": None,
                        "license_identifier": None,
                        "license_status": "UNRESOLVED",
                        "unresolved_reason": "No exact installed distribution or reviewed system component mapping was found.",
                        "notice_files": [],
                    }
                )
                continue
        if distribution is not None:
            metadata_name = distribution.metadata.get("Name") or owner
            version = distribution.version
            license_id = distribution.metadata.get(
                "License-Expression"
            ) or distribution.metadata.get("License")
            files = distribution_license_files(distribution)
            supplement = supplements.get(normalized_distribution_name(metadata_name))
        else:
            metadata_name = "CPython"
        if supplement:
            license_id = supplement.get("license_identifier") or license_id
            supplemental_files = [
                (
                    "supplemental/" + Path(supplement["license_file"]).name,
                    Path(supplement["license_file"]),
                )
            ]
            files.extend(supplemental_files)
            exception_file = supplement.get("exception_file")
            if exception_file:
                files.append(("supplemental/" + Path(exception_file).name, Path(exception_file)))
        else:
            native_rule = native_review.get(owner)
            if native_rule:
                supplement = native_rule
        if not license_id:
            reason = "Installed distribution metadata does not declare a license identifier and no exact supplemental record applies."
        elif not files:
            reason = "No exact distribution-provided or reviewed supplemental license/notice text is available."
        else:
            reason = None
        native_reason = supplement.get("native_unresolved_reason") if supplement else None
        if native_reason:
            reason = native_reason
        elif supplement and supplement.get("status", "").startswith("UNRESOLVED"):
            reason = (
                supplement.get("reason")
                or "The reviewed registry leaves this native component unresolved."
            )
        copied: list[dict[str, str]] = []
        for relative_source, source_path in sorted(files, key=lambda row: row[0].casefold()):
            if not source_path.is_file():
                reason = (
                    reason or "A referenced license text is missing from this exact environment."
                )
                continue
            if relative_source.startswith("supplemental/"):
                if supplement is None:
                    reason = "Supplemental license file has no reviewed registry record."
                    continue
                expected_sha = supplement.get("license_sha256")
                if relative_source.endswith(
                    Path(supplement.get("exception_file", "__none__")).name
                ):
                    expected_sha = supplement.get("exception_sha256")
                if expected_sha and sha256_file(source_path) != expected_sha:
                    reason = (
                        "A supplemental license text digest does not match the reviewed registry."
                    )
                    continue
            safe_component = (
                re.sub(r"[^a-z0-9.-]+", "-", owner.casefold()).strip("-") or "component"
            )
            safe_source = safe_posix_path(relative_source)
            if safe_source is None:
                reason = "A license evidence path is unsafe."
                continue
            destination = Path("THIRD_PARTY_LICENSES") / safe_component / safe_source
            digest = copy_text_evidence(source_path, output_root / destination)
            notice = {
                "component_id": owner,
                "component_version": version or "unknown",
                "path": destination.as_posix(),
                "sha256": digest,
                "source_reference": (
                    supplement.get("upstream_reference")
                    if supplement and relative_source.startswith("supplemental/")
                    else "installed_distribution_file_metadata"
                ),
            }
            copied.append(notice)
            notice_rows.append(notice)
        if not license_id or not copied or reason:
            unresolved.add(f"component:{owner}")
            status = "UNRESOLVED"
        else:
            status = "EVIDENCE_PRESENT"
        component_rows.append(
            {
                "component_id": owner,
                "version": version,
                "license_identifier": license_id,
                "license_status": status,
                "unresolved_reason": reason,
                "notice_files": [row["path"] for row in copied],
            }
        )
    return component_rows, notice_rows, unresolved


def build_inventory(
    stage_root: Path,
    toc_path: Path,
    analysis_path: Path,
    contents_dir: str,
    project_root: Path,
    revision: str,
    studio_version: str,
    registry_path: Path,
    evidence_root: Path,
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    if not BUILD_REVISION.fullmatch(revision) or not SEMVER.fullmatch(studio_version):
        raise ValueError("Build revision or semantic Studio version is invalid")
    stage_root = stage_root.resolve(strict=True)
    project_root = project_root.resolve(strict=True)
    evidence_root = evidence_root.resolve()
    if (
        not stage_root.is_dir()
        or stage_root == project_root
        or evidence_root == stage_root
        or stage_root in evidence_root.parents
    ):
        raise ValueError("The staging directory is invalid")
    evidence_root.mkdir(parents=True, exist_ok=True)
    if any(evidence_root.iterdir()):
        raise ValueError("The compliance evidence directory must be empty")
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    toc = toc_destinations(read_toc(toc_path), contents_dir, stage_root)
    analysis_sources = analysis_source_paths(analysis_path)
    distributions = list(importlib.metadata.distributions())
    source_owners, by_name = distribution_source_index(distributions)
    project_norm = norm_source(project_root)
    runtime_root_norm = norm_source(Path(sys.base_prefix))
    all_paths = sorted(
        (path for path in stage_root.rglob("*") if path.is_file()), key=lambda item: item.as_posix()
    )
    if not all_paths:
        raise ValueError("The staging directory is empty")
    records: list[dict[str, Any]] = []
    package_owners: set[str] = set()
    unresolved_items: set[str] = set()
    toc_seen: set[str] = set()
    analysis_component_owners: set[str] = set()
    for raw_source in analysis_sources:
        source = Path(raw_source)
        key = norm_source(source)
        matches = source_owners.get(key, [])
        analysis_component_owners.update(
            normalized_distribution_name(match.metadata.get("Name", "unknown")) for match in matches
        )
        if is_python_runtime_source(source, runtime_root_norm):
            analysis_component_owners.add("cpython-runtime")
        if key.startswith(project_norm + os.sep):
            analysis_component_owners.add("packlab-application")
    for path in all_paths:
        relative = path.relative_to(stage_root).as_posix()
        row = toc.get(relative)
        toc_kind: str | None = None
        source_path: Path | None = None
        owner_ids: set[str] = set()
        mapping_evidence = "unmapped"
        unresolved_reason: str | None = None
        if row is not None:
            raw_source, toc_kind = row
            toc_seen.add(relative)
            source_path = Path(raw_source) if raw_source else None
            if Path(relative).name == "packlab-build-provenance.json":
                owner_ids.add("packlab-build-provenance")
                mapping_evidence = "build_generated_path_free_provenance"
            elif toc_kind in {"EXECUTABLE", "PKG"}:
                owner_ids.update(analysis_component_owners)
                owner_ids.update({"packlab-application", "pyinstaller-bootloader"})
                mapping_evidence = "pyinstaller_analysis_and_collect_toc_composite"
            elif source_path is not None and source_path.exists():
                key = norm_source(source_path)
                matches = source_owners.get(key, [])
                if matches:
                    owner_ids.update(
                        normalized_distribution_name(item.metadata.get("Name", "unknown"))
                        for item in matches
                    )
                    if sha256_file(source_path) == sha256_file(path):
                        mapping_evidence = (
                            "pyinstaller_collect_toc_and_exact_distribution_file_hash"
                        )
                    else:
                        mapping_evidence = "pyinstaller_collect_toc_distribution_file_hash_mismatch"
                        unresolved_reason = "The collected file does not match the installed distribution source bytes."
                elif key.startswith(project_norm + os.sep):
                    owner_ids.add("packlab-application")
                    if sha256_file(source_path) == sha256_file(path):
                        mapping_evidence = "pyinstaller_collect_toc_and_packlab_source_hash"
                    else:
                        mapping_evidence = "pyinstaller_collect_toc_packlab_source_hash_mismatch"
                        unresolved_reason = (
                            "The staged PackLab file differs from its declared source file."
                        )
                elif is_windows_api_runtime(source_path) and is_python_runtime_source(
                    source_path, runtime_root_norm
                ):
                    owner_ids.add("microsoft-windows-runtime")
                    mapping_evidence = "pyinstaller_collect_toc_python_distribution_runtime_file"
                    unresolved_reason = "Microsoft/system runtime redistribution evidence is not reviewed for this exact staged file."
                elif is_python_runtime_source(source_path, runtime_root_norm):
                    owner_ids.add("cpython-runtime")
                    mapping_evidence = "pyinstaller_collect_toc_python_runtime_source"
                elif source_path.exists():
                    owner_ids.add("unmapped-source-component")
                    mapping_evidence = "pyinstaller_collect_toc_unclassified_source"
                    unresolved_reason = "The TOC source is outside the project, Python runtime, and installed distributions."
            else:
                unresolved_reason = (
                    "The PyInstaller TOC entry has no source file to support component mapping."
                )
        if not owner_ids and relative == "THIRD_PARTY_NOTICES.txt":
            owner_ids.add("packlab-compliance-notices")
            mapping_evidence = "generated_compliance_notice"
        elif (
            not owner_ids
            and relative.startswith("THIRD_PARTY_LICENSES/")
            and path.suffix.lower() in TEXT_LICENSE_SUFFIXES
        ):
            owner_ids.add("packlab-compliance-license-evidence")
            mapping_evidence = "generated_compliance_license_text"
        if not owner_ids:
            unresolved_reason = (
                unresolved_reason
                or "No exact TOC, installed distribution, Python runtime, or PackLab source mapping was found."
            )
        package_owners.update(owner_ids)
        if unresolved_reason:
            unresolved_items.add(f"file:{relative}")
        records.append(
            {
                "relative_path": relative,
                "sha256": sha256_file(path),
                "byte_length": path.stat().st_size,
                "file_category": category_for(relative, toc_kind, source_path),
                "component_ids": sorted(owner_ids),
                "component_versions": {},
                "mapping_method": mapping_evidence,
                "pe_metadata": read_pe_metadata(path),
                "license_identifier": None,
                "license_status": "PENDING_COMPONENT_REVIEW",
                "required_notice_files": [],
                "unresolved_reason": unresolved_reason,
            }
        )
    dangling_toc = sorted(set(toc) - toc_seen)
    for relative in dangling_toc:
        unresolved_items.add(f"toc:{relative}")
    owners_to_review = {
        owner
        for owner in package_owners
        if owner
        not in {
            "packlab-application",
            "packlab-build-provenance",
            "packlab-compliance-notices",
            "packlab-compliance-license-evidence",
        }
    }
    if "pyinstaller-bootloader" in owners_to_review:
        owners_to_review.add("pyinstaller")
    if "cadquery-ocp-novtk" in owners_to_review:
        owners_to_review.add("occt-7.9.3")
    component_rows, notice_rows, component_unresolved = license_rows(
        owners_to_review, by_name, registry, evidence_root
    )
    unresolved_items.update(component_unresolved)
    component_by_id = {row["component_id"]: row for row in component_rows}
    for file_record in records:
        mapped_components = [
            component_by_id[owner]
            for owner in file_record["component_ids"]
            if owner in component_by_id
        ]
        file_record["component_versions"] = {
            row["component_id"]: row["version"] for row in mapped_components
        }
        file_record["license_identifier"] = "; ".join(
            sorted(
                {
                    row["license_identifier"]
                    for row in mapped_components
                    if row["license_identifier"]
                }
            )
        ) or ("PackLab-owned" if file_record["component_ids"] else None)
        file_record["license_status"] = (
            "UNRESOLVED"
            if file_record["unresolved_reason"]
            or any(row["license_status"] == "UNRESOLVED" for row in mapped_components)
            else "EVIDENCE_PRESENT"
        )
        file_record["required_notice_files"] = sorted(
            {path for row in mapped_components for path in row["notice_files"]}
        )
        if file_record["license_status"] == "UNRESOLVED" and not file_record["unresolved_reason"]:
            file_record["unresolved_reason"] = (
                "At least one mapped component lacks complete license/notice evidence."
            )
    provenance_files = [
        item
        for item in records
        if Path(item["relative_path"]).name == "packlab-build-provenance.json"
    ]
    if len(provenance_files) != 1:
        unresolved_items.add("component:build-provenance")
    else:
        embedded_path = stage_root / PurePosixPath(provenance_files[0]["relative_path"])
        embedded = json.loads(embedded_path.read_text(encoding="utf-8"))
        if (
            embedded.get("PACKLAB_BUILD_REVISION") != revision
            or embedded.get("studio_version") != studio_version
        ):
            unresolved_items.add("component:build-provenance")
            provenance_files[0]["unresolved_reason"] = (
                "Embedded build provenance does not match the inventory inputs."
            )
            provenance_files[0]["license_status"] = "UNRESOLVED"
    notices_lines = [
        "PackLab Studio third-party notices",
        f"Build revision: {revision}",
        f"Studio version: {studio_version}",
        "This file is a generated index of the component evidence shipped beside it.",
        "",
    ]
    for component in sorted(component_rows, key=lambda item: item["component_id"].casefold()):
        notices_lines.append(
            f"{component['component_id']} {component['version'] or 'version unavailable'} — "
            f"{component['license_identifier'] or 'license identifier unresolved'}"
        )
        for license_file in component["notice_files"]:
            notices_lines.append(f"  {license_file}")
        if component["unresolved_reason"]:
            notices_lines.append(f"  UNRESOLVED: {component['unresolved_reason']}")
        notices_lines.append("")
    (evidence_root / "THIRD_PARTY_LICENSES").mkdir(exist_ok=True)
    (evidence_root / "THIRD_PARTY_NOTICES.txt").write_text(
        "\n".join(notices_lines), encoding="utf-8", newline="\n"
    )
    staged_bytes = sum(item["byte_length"] for item in records)
    validation = {
        "schema_version": SCHEMA_VERSION,
        "PACKLAB_BUILD_REVISION": revision,
        "studio_version": studio_version,
        "staged_file_count": len(records),
        "staged_total_bytes": staged_bytes,
        "mapped_file_count": sum(bool(item["component_ids"]) for item in records),
        "unresolved_file_count": sum(item["license_status"] == "UNRESOLVED" for item in records),
        "unresolved_component_count": sum(
            row["license_status"] == "UNRESOLVED" for row in component_rows
        ),
        "unresolved_count": len(unresolved_items),
        "required_notice_count": sum(bool(row["license_identifier"]) for row in component_rows),
        "collected_notice_count": len(notice_rows),
        "status": "CLEARED_FOR_PL0350_PACKAGING" if not unresolved_items else "BLOCKED",
        "unresolved_items": sorted(unresolved_items),
    }
    inventory = {
        "schema_version": SCHEMA_VERSION,
        "PACKLAB_BUILD_REVISION": revision,
        "studio_version": studio_version,
        "staged_file_count": len(records),
        "staged_total_bytes": staged_bytes,
        "files": sorted(records, key=lambda item: item["relative_path"].casefold()),
    }
    summary = {
        "schema_version": SCHEMA_VERSION,
        "PACKLAB_BUILD_REVISION": revision,
        "studio_version": studio_version,
        "components": sorted(component_rows, key=lambda item: item["component_id"].casefold()),
        "pyinstaller_toc_unmatched_destinations": dangling_toc,
    }
    return inventory, summary, [validation, {"notices": notice_rows}]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging-dir", type=Path, required=True)
    parser.add_argument("--collect-toc", type=Path, required=True)
    parser.add_argument("--analysis-toc", type=Path, required=True)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--build-revision", required=True)
    parser.add_argument("--studio-version", required=True)
    parser.add_argument("--contents-dir", default="_internal")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        inventory, summary, evidence = build_inventory(
            args.staging_dir,
            args.collect_toc,
            args.analysis_toc,
            args.contents_dir,
            args.project_root,
            args.build_revision,
            args.studio_version,
            args.registry,
            args.output_dir,
        )
        validation = evidence[0]
        canonical_json(args.output_dir / "windows-redistribution-inventory.json", inventory)
        canonical_json(args.output_dir / "windows-component-summary.json", summary)
        canonical_json(args.output_dir / "compliance-validation.json", validation)
        canonical_json(args.output_dir / "license-evidence-manifest.json", evidence[1])
        for output_file in args.output_dir.rglob("*"):
            if output_file.is_file() and output_file.suffix.lower() in {
                ".exe",
                ".dll",
                ".pyd",
                ".zip",
                ".pyz",
                ".pkg",
            }:
                raise ValueError("Binary content is forbidden in pre-clearance compliance evidence")
        print(
            f"Compliance status: {validation['status']}; "
            f"staged files: {validation['staged_file_count']}; "
            f"unresolved items: {validation['unresolved_count']}"
        )
        return 0 if validation["unresolved_count"] == 0 else 2
    except (OSError, ValueError, json.JSONDecodeError, SyntaxError) as error:
        # Exception strings from filesystem/library errors may contain runner paths.
        print(f"Compliance inventory generation failed: {type(error).__name__}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
