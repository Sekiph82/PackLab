"""Fail-closed validator for the controlled Windows native source lock."""

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
AUTHORITATIVE_SOURCE_HOSTS = {"download.qt.io", "files.pythonhosted.org", "github.com"}
WILDCARD_RE = re.compile(r"[*?\[\]]")
MUTABLE_URL_RE = re.compile(r"/(?:refs/heads/|(?:main|master|latest)(?:/|$))", re.IGNORECASE)
REQUIRED_RECORD_FIELDS = {
    "id",
    "component",
    "version",
    "build",
    "url",
    "sha256",
    "license_identifier",
    "license_notice_source",
    "source_availability_role",
    "production_purpose",
    "retained_runtime_surface",
}


class SourceLockError(ValueError):
    """Raised when the native source lock is incomplete or mutable."""


def validate_source_lock(data: dict[str, Any]) -> None:
    if data.get("schema_version") != 1:
        raise SourceLockError("schema_version must be 1")
    records = data.get("records")
    if not isinstance(records, list) or not records:
        raise SourceLockError("records must be a non-empty list")

    by_id: dict[str, dict[str, Any]] = {}
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise SourceLockError(f"record {index} must be an object")
        missing = sorted(REQUIRED_RECORD_FIELDS - record.keys())
        if missing:
            raise SourceLockError(
                f"record {index} is missing required fields: {', '.join(missing)}"
            )
        record_id = record["id"]
        if not isinstance(record_id, str) or not record_id.strip():
            raise SourceLockError(f"record {index} has an invalid id")
        if record_id in by_id:
            raise SourceLockError(f"duplicate record id: {record_id}")
        by_id[record_id] = record

        for field in ("version", "build"):
            value = record[field]
            if not isinstance(value, str) or not value.strip():
                raise SourceLockError(f"{record_id}.{field} must be a non-empty exact string")
            if WILDCARD_RE.search(value):
                raise SourceLockError(f"{record_id}.{field} contains a wildcard selector")

        digest = record["sha256"]
        if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
            raise SourceLockError(f"{record_id}.sha256 must be a lowercase 64-character SHA-256")

        url = record["url"]
        parsed = urlparse(url) if isinstance(url, str) else None
        if parsed is None or parsed.scheme != "https" or not parsed.netloc:
            raise SourceLockError(f"{record_id}.url must be an authoritative HTTPS URL")
        if parsed.query or parsed.fragment or MUTABLE_URL_RE.search(parsed.path):
            raise SourceLockError(f"{record_id}.url is mutable")
        if parsed.hostname not in AUTHORITATIVE_SOURCE_HOSTS:
            raise SourceLockError(f"{record_id}.url uses an unapproved source host")

        for field in (
            "component",
            "license_identifier",
            "license_notice_source",
            "source_availability_role",
            "production_purpose",
        ):
            if not isinstance(record[field], str) or not record[field].strip():
                raise SourceLockError(f"{record_id}.{field} must be a non-empty string")
        surface = record["retained_runtime_surface"]
        if (
            not isinstance(surface, list)
            or not surface
            or any(not isinstance(item, str) or not item.strip() for item in surface)
        ):
            raise SourceLockError(
                f"{record_id}.retained_runtime_surface must list covered runtime files"
            )
        notice_url = urlparse(record["license_notice_source"])
        if (
            notice_url.scheme != "https"
            or not notice_url.netloc
            or notice_url.hostname != "github.com"
            or notice_url.query
            or notice_url.fragment
            or MUTABLE_URL_RE.search(notice_url.path)
        ):
            raise SourceLockError(f"{record_id}.license_notice_source must be immutable HTTPS")

        corresponding = record.get("corresponding_source_ids", [])
        if not isinstance(corresponding, list) or any(
            not isinstance(item, str) for item in corresponding
        ):
            raise SourceLockError(f"{record_id}.corresponding_source_ids must be a string list")
        if record["source_availability_role"] == "PROJECT_OFFICIAL_BINARY":
            if (
                not isinstance(record.get("package_name"), str)
                or not record["package_name"].strip()
            ):
                raise SourceLockError(
                    f"{record_id}.package_name is required for an official binary"
                )
            if not corresponding:
                raise SourceLockError(f"{record_id} must bind its corresponding source IDs")

    components = data.get("production_components")
    if not isinstance(components, dict) or not components:
        raise SourceLockError("production_components must be a non-empty object")
    referenced: set[str] = set()
    for component, source_ids in components.items():
        if not isinstance(component, str) or not isinstance(source_ids, list) or not source_ids:
            raise SourceLockError(
                "every production component must reference at least one source record"
            )
        for source_id in source_ids:
            if source_id not in by_id:
                raise SourceLockError(
                    f"production component {component} references unknown source {source_id}"
                )
            referenced.add(source_id)

    required_ids = data.get("required_source_ids")
    if not isinstance(required_ids, list) or not required_ids:
        raise SourceLockError("required_source_ids must be a non-empty list")
    for source_id in required_ids:
        if source_id not in by_id:
            raise SourceLockError(f"required source is unreferenced or missing: {source_id}")
        if source_id not in referenced:
            raise SourceLockError(
                f"required source is not used by a production component: {source_id}"
            )

    for record_id, record in by_id.items():
        for source_id in record.get("corresponding_source_ids", []):
            if source_id not in by_id:
                raise SourceLockError(
                    f"{record_id} references unknown corresponding source {source_id}"
                )

    lock = data.get("build_environment_lock")
    if not isinstance(lock, dict) or set(("path", "sha256", "platform")) - lock.keys():
        raise SourceLockError("build_environment_lock must bind path, sha256, and platform")
    if not isinstance(lock["path"], str) or not lock["path"].strip():
        raise SourceLockError("build_environment_lock.path must be non-empty")
    if not isinstance(lock["sha256"], str) or not SHA256_RE.fullmatch(lock["sha256"]):
        raise SourceLockError("build_environment_lock.sha256 must be an exact lowercase SHA-256")
    if lock["platform"] != "win-64":
        raise SourceLockError("build environment must target the exact win-64 platform")


def load_source_lock(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SourceLockError("source lock root must be an object")
    validate_source_lock(data)
    return data


def verify_uv_lock_binding(data: dict[str, Any], uv_lock_path: Path) -> None:
    try:
        uv_data = tomllib.loads(uv_lock_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as error:
        raise SourceLockError("uv.lock could not be read") from error
    packages = uv_data.get("package")
    if not isinstance(packages, list):
        raise SourceLockError("uv.lock has no package records")
    by_name_version = {
        (item.get("name"), item.get("version")): item for item in packages if isinstance(item, dict)
    }
    for record in data["records"]:
        if record["source_availability_role"] != "PROJECT_OFFICIAL_BINARY":
            continue
        package = by_name_version.get((record["package_name"], record["version"]))
        if package is None:
            raise SourceLockError(f"{record['id']} is absent from uv.lock")
        expected = (record["url"], f"sha256:{record['sha256']}")
        wheels = package.get("wheels", [])
        if not any((wheel.get("url"), wheel.get("hash")) == expected for wheel in wheels):
            raise SourceLockError(f"{record['id']} URL/SHA-256 does not match uv.lock")


def verify_conda_lock(lock_path: Path) -> None:
    """Require a single-platform conda-lock file with exact artifact identities."""
    try:
        content = lock_path.read_text(encoding="utf-8")
    except OSError as error:
        raise SourceLockError("conda build-environment lock could not be read") from error
    platforms = re.findall(r"(?m)^\s+- (win-64|linux-64|osx-64|osx-arm64)$", content)
    if platforms != ["win-64"]:
        raise SourceLockError("conda build-environment lock must contain only win-64")
    package_starts = list(re.finditer(r"(?m)^- name: ([^\r\n]+)$", content))
    if not package_starts:
        raise SourceLockError("conda build-environment lock has no package records")
    seen: set[str] = set()
    for index, start in enumerate(package_starts):
        end = package_starts[index + 1].start() if index + 1 < len(package_starts) else len(content)
        block = content[start.start() : end]
        name = start.group(1).strip()
        if name in seen:
            raise SourceLockError(f"conda build-environment lock duplicates package {name}")
        seen.add(name)
        version = re.search(r"(?m)^  version: ([^\r\n]+)$", block)
        url = re.search(r"(?m)^  url: (https://[^\s]+)$", block)
        digest = re.search(r"(?m)^    sha256: ([0-9a-f]{64})$", block)
        if not version or WILDCARD_RE.search(version.group(1)):
            raise SourceLockError(f"conda package {name} has no exact version identity")
        exact_version = version.group(1).strip("'\"")
        if not url or MUTABLE_URL_RE.search(url.group(1)):
            raise SourceLockError(f"conda package {name} has no immutable HTTPS artifact URL")
        artifact_name = urlparse(url.group(1)).path.rsplit("/", 1)[-1]
        if (
            urlparse(url.group(1)).hostname != "conda.anaconda.org"
            or urlparse(url.group(1)).query
            or urlparse(url.group(1)).fragment
            or WILDCARD_RE.search(artifact_name)
            or not artifact_name.startswith(f"{name}-{exact_version}-")
            or not artifact_name.endswith((".conda", ".tar.bz2"))
        ):
            raise SourceLockError(f"conda package {name} URL has no exact package/build filename")
        if not digest:
            raise SourceLockError(f"conda package {name} has no exact SHA-256")


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--lock", type=Path, default=Path("tools/packaging/windows_native_source_lock.json")
    )
    parser.add_argument("--verify-build-lock", action="store_true")
    parser.add_argument("--verify-uv-lock", action="store_true")
    parser.add_argument("--verify-conda-lock", action="store_true")
    args = parser.parse_args()
    data = load_source_lock(args.lock)
    project_root = args.lock.parents[2]
    if args.verify_build_lock:
        lock_path = project_root / data["build_environment_lock"]["path"]
        actual = __import__("hashlib").sha256(lock_path.read_bytes()).hexdigest()
        if actual != data["build_environment_lock"]["sha256"]:
            raise SourceLockError("conda build-environment lock digest does not match source lock")
    if args.verify_uv_lock:
        verify_uv_lock_binding(data, project_root / "uv.lock")
    if args.verify_conda_lock:
        verify_conda_lock(project_root / data["build_environment_lock"]["path"])
    print(
        f"WINDOWS_NATIVE_SOURCE_LOCK_PASS records={len(data['records'])} sha256={__import__('hashlib').sha256(args.lock.read_bytes()).hexdigest()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
