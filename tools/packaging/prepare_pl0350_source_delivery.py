"""Stage hash-verified corresponding source and relinking evidence for PL-0350."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from tools.packaging.validate_windows_native_source_lock import load_source_lock

ROLES = {
    "SOURCE_BUILD_INPUT",
    "CORRESPONDING_SOURCE_AND_NOTICES",
    "CORRESPONDING_SOURCE_AND_THIRD_PARTY_INVENTORY",
    "CORRESPONDING_SOURCE_AND_NOTICE",
}
OPEN3D_ID = "open3d-attested-source-d32b4fce"
OPEN3D: dict[str, object] = {
    "id": OPEN3D_ID,
    "component": "Open3D",
    "version": "0.20.0",
    "revision": "d32b4fce639b3cde284184072796480ef9b528d1",
    "url": "https://github.com/isl-org/Open3D/archive/d32b4fce639b3cde284184072796480ef9b528d1.tar.gz",
    "sha256": "4d527f246843e7a5920433535d0fcfb26f093706ac3fc7642bb57e39a917d0b1",
    "byte_length": 52728300,
    "license_identifier": "MIT",
    "component_ids": ["open3d"],
}
OPEN3D_LINKED_SOURCES: list[dict[str, object]] = [
    {
        "id": "open3d-libzmq-source-4.3.5",
        "component": "ZeroMQ static link dependency",
        "version": "4.3.5",
        "revision": "v4.3.5",
        "url": "https://github.com/zeromq/libzmq/releases/download/v4.3.5/zeromq-4.3.5.tar.gz",
        "sha256": "6653ef5910f17954861fe72332e68b03ca6e4d9c7160eb3a8de5a5a913bfab43",
        "license_identifier": "LGPL-3.0-or-later WITH ZeroMQ-static-linking-exception",
        "source_availability_role": "CORRESPONDING_SOURCE_AND_THIRD_PARTY_INVENTORY",
        "component_ids": ["open3d"],
    },
    {
        "id": "open3d-cppzmq-source-4.10.0",
        "component": "cppzmq header-only link dependency",
        "version": "4.10.0",
        "revision": "v4.10.0",
        "url": "https://github.com/zeromq/cppzmq/archive/refs/tags/v4.10.0.tar.gz",
        "sha256": "c81c81bba8a7644c84932225f018b5088743a22999c6d82a2b5f5cd1e6942b74",
        "license_identifier": "MIT",
        "source_availability_role": "CORRESPONDING_SOURCE_AND_THIRD_PARTY_INVENTORY",
        "component_ids": ["open3d"],
    },
]
COMPONENTS = {
    "ocp-source-7.9.3.1.1": ["packlab-controlled-ocp"],
    "ocp-pywrap-source-9251940": ["packlab-controlled-ocp"],
    "occt-source-7.9.3": ["occt-7.9.3"],
    "fmt-source-12.1.0": ["fmt-12.1.0"],
    "pyside-source-6.11.2": ["pyside6-addons", "pyside6-essentials", "shiboken6"],
    "qtbase-source-6.11.2": ["pyside6-addons", "pyside6-essentials"],
    "qtsvg-source-6.11.2": ["pyside6-addons"],
    "qtpdf-pdfium-source-6.11.2": ["pyside6-addons"],
    "onetbb-source-2021.12.0": ["open3d"],
}


def digest_file(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size


def _fetch(record: dict[str, object], target: Path) -> None:
    request = Request(str(record["url"]), headers={"User-Agent": "PackLab-PL0350-source/1"})
    digest = hashlib.sha256()
    size = 0
    target.parent.mkdir(parents=True, exist_ok=True)
    with urlopen(request, timeout=180) as response, target.open("wb") as output:
        while chunk := response.read(1024 * 1024):
            digest.update(chunk)
            output.write(chunk)
            size += len(chunk)
    if digest.hexdigest() != record["sha256"] or (
        record.get("byte_length") is not None and size != record["byte_length"]
    ):
        target.unlink(missing_ok=True)
        raise ValueError(f"Exact corresponding-source archive verification failed: {record['id']}")


def prepare(
    source_root: Path,
    stage_root: Path,
    project_root: Path,
    revision: str,
    studio_version: str,
) -> dict[str, object]:
    lock_path = project_root / "tools/packaging/windows_native_source_lock.json"
    lock = load_source_lock(lock_path)
    records: list[dict[str, object]] = []
    for locked in lock["records"]:
        if locked["source_availability_role"] not in ROLES:
            continue
        if locked["id"] == "open3d-source-0.20.0":
            # The historical lock points at a different source commit than the attested wheel.
            continue
        filename = Path(urlparse(locked["url"]).path).name
        fetched = source_root / f"{locked['id']}--{filename}"
        digest, size = digest_file(fetched)
        if digest != locked["sha256"]:
            raise ValueError(f"Previously fetched source archive changed: {locked['id']}")
        record = {
            "id": locked["id"],
            "component": locked["component"],
            "version": locked["version"],
            "revision": locked["revision"],
            "url": locked["url"],
            "sha256": locked["sha256"],
            "byte_length": size,
            "license_identifier": locked["license_identifier"],
            "source_availability_role": locked["source_availability_role"],
            "component_ids": COMPONENTS.get(locked["id"], []),
            "source_filename": filename,
            "verified_source_path": fetched,
        }
        records.append(record)
    open3d = dict(OPEN3D)
    open3d_path = source_root / f"{OPEN3D_ID}--{Path(urlparse(str(OPEN3D['url'])).path).name}"
    if not open3d_path.is_file():
        _fetch(open3d, open3d_path)
    digest, size = digest_file(open3d_path)
    if digest != OPEN3D["sha256"] or size != OPEN3D["byte_length"]:
        raise ValueError("Attested Open3D corresponding-source archive identity mismatch")
    open3d["source_filename"] = open3d_path.name.split("--", 1)[1]
    open3d["source_availability_role"] = "CORRESPONDING_SOURCE_AND_THIRD_PARTY_INVENTORY"
    open3d["verified_source_path"] = open3d_path
    records.append(open3d)

    for linked_source in OPEN3D_LINKED_SOURCES:
        linked = dict(linked_source)
        filename = Path(urlparse(str(linked["url"])).path).name
        archive = source_root / f"{linked['id']}--{filename}"
        if not archive.is_file():
            _fetch(linked, archive)
        digest, size = digest_file(archive)
        if digest != linked["sha256"]:
            raise ValueError(f"Open3D linked source identity mismatch: {linked['id']}")
        linked["source_filename"] = filename
        linked["byte_length"] = size
        linked["verified_source_path"] = archive
        records.append(linked)

    delivery_root = stage_root / "COMPLIANCE" / "CORRESPONDING_SOURCE"
    for record in records:
        source_path = Path(str(record.pop("verified_source_path")))
        destination = delivery_root / str(record["id"]) / str(record["source_filename"])
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_path, destination)
        observed, size = digest_file(destination)
        if observed != record["sha256"] or size != record["byte_length"]:
            raise ValueError(f"Staged source archive identity mismatch: {record['id']}")
        record["path"] = destination.relative_to(stage_root).as_posix()

    manifest: dict[str, object] = {
        "schema_version": 1,
        "status": "PASS",
        "PACKLAB_BUILD_REVISION": revision,
        "studio_version": studio_version,
        "source_lock_sha256": hashlib.sha256(lock_path.read_bytes()).hexdigest(),
        "records": sorted(records, key=lambda row: str(row["id"])),
        "notice_corpus": {
            "path": "COMPLIANCE/THIRD_PARTY_LICENSES/Open3D/OPEN3D-THIRD-PARTY-LICENSES.txt",
            "sha256": "7a396b9b879b9d5ade9aadf505386199ff2a3f84fe6f4e4ec3e1d9f817fd1e34",
        },
        "open3d_sbom": {
            "path": "COMPLIANCE/EVIDENCE/PL-0350_OPEN3D_WHEEL_NATIVE_SBOM_38617631153.json",
            "sha256": "",
        },
        "relinking_guide": {
            "path": "COMPLIANCE/CORRESPONDING_SOURCE/RELINKING_AND_SOURCE_GUIDE.txt",
            "sha256": "",
        },
    }
    guide_source = project_root / "tools/packaging/windows_licenses/RELINKING_AND_SOURCE_GUIDE.txt"
    guide_target = stage_root / "COMPLIANCE/CORRESPONDING_SOURCE/RELINKING_AND_SOURCE_GUIDE.txt"
    shutil.copyfile(guide_source, guide_target)
    manifest["relinking_guide"]["sha256"] = digest_file(guide_target)[0]  # type: ignore[index]
    notice_source = (
        project_root
        / "tools/packaging/windows_licenses/Open3D-0.20.0/OPEN3D-THIRD-PARTY-LICENSES.txt"
    )
    notice_target = (
        stage_root / "COMPLIANCE/THIRD_PARTY_LICENSES/Open3D/OPEN3D-THIRD-PARTY-LICENSES.txt"
    )
    notice_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(notice_source, notice_target)
    if digest_file(notice_target)[0] != manifest["notice_corpus"]["sha256"]:  # type: ignore[index]
        raise ValueError("Open3D third-party notice corpus does not match its pinned digest")
    sbom_source = (
        project_root
        / "coordination/sessions/M16-C001/evidence/PL-0350_OPEN3D_WHEEL_NATIVE_SBOM_38617631153.json"
    )
    sbom_target = (
        stage_root / "COMPLIANCE/EVIDENCE/PL-0350_OPEN3D_WHEEL_NATIVE_SBOM_38617631153.json"
    )
    sbom_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(sbom_source, sbom_target)
    manifest["open3d_sbom"]["sha256"] = digest_file(sbom_target)[0]  # type: ignore[index]
    manifest_path = stage_root / "COMPLIANCE/CORRESPONDING_SOURCE/source-delivery-manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--stage-root", type=Path, required=True)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--revision", required=True)
    parser.add_argument("--studio-version", required=True)
    args = parser.parse_args()
    result = prepare(
        args.source_root, args.stage_root, args.project_root, args.revision, args.studio_version
    )
    records = result["records"]
    if not isinstance(records, list):
        raise ValueError("Source-delivery manifest did not return a source record list.")
    print(
        f"PL0350_SOURCE_DELIVERY_PASS count={len(records)} source_lock_sha256={result['source_lock_sha256']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
