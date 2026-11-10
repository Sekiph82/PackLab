"""Verify local YCB sample provenance and extraction integrity."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import tarfile
from pathlib import Path, PurePosixPath, PureWindowsPath

if __package__:
    from tools.datasets.ycb_source_identity import (
        YCB_ARCHIVE_IDENTITIES,
        YCB_INDEX_URL,
        YCB_LICENSE_URL,
    )
else:
    from ycb_source_identity import (  # type: ignore[no-redef]
        YCB_ARCHIVE_IDENTITIES,
        YCB_INDEX_URL,
        YCB_LICENSE_URL,
    )


DATASET_ID = "packlab-m17-ycb-real-reference-v1"
MAX_RECORD_BYTES = 100 * 1024 * 1024


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _regular_file(root: Path, relative: str, max_bytes: int = MAX_RECORD_BYTES) -> Path:
    path = PurePosixPath(relative)
    windows_path = PureWindowsPath(relative)
    if (
        not relative
        or "\x00" in relative
        or ":" in relative
        or windows_path.drive
        or windows_path.is_absolute()
        or path.is_absolute()
        or "\\" in relative
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise ValueError(f"unsafe source record path: {relative!r}")
    target = root.joinpath(*path.parts)
    for candidate in (target, *target.parents):
        if candidate == root.parent:
            break
        if candidate.is_symlink() or (
            hasattr(candidate, "is_junction") and candidate.is_junction()
        ):
            raise ValueError(f"linked source record path: {relative}")
    if not target.is_file():
        raise ValueError(f"missing or linked source record: {relative}")
    try:
        target.resolve(strict=True).relative_to(root)
    except ValueError as exc:
        raise ValueError(f"source record escapes dataset root: {relative}") from exc
    if target.stat().st_size > max_bytes:
        raise ValueError(f"source record exceeds size limit: {relative}")
    return target


def _check_file(root: Path, record: dict) -> int:
    relative = record.get("path")
    if type(relative) is not str:
        raise ValueError("source record path must be a string")
    target = _regular_file(root, relative)
    size = record.get("bytes")
    digest = record.get("sha256")
    if (
        type(size) is not int
        or size != target.stat().st_size
        or type(digest) is not str
        or not re.fullmatch(r"[0-9a-f]{64}", digest)
        or _sha256(target) != digest
    ):
        raise ValueError(f"source file length/hash mismatch: {relative}")
    return size


def _verify_archive_members(archive_path: Path, records: list[dict], member_key: str) -> None:
    expected: dict[str, dict] = {}
    for record in records:
        member_name = record.get(member_key)
        if (
            type(member_name) is not str
            or not member_name
            or "\\" in member_name
            or ":" in member_name
            or PurePosixPath(member_name).is_absolute()
            or PureWindowsPath(member_name).drive
            or any(part in {"", ".", ".."} for part in PurePosixPath(member_name).parts)
        ):
            raise ValueError("unsafe or missing YCB archive member path")
        if member_name in expected:
            raise ValueError(f"duplicate YCB archive member record: {member_name}")
        expected[member_name] = record
    seen: set[str] = set()
    with tarfile.open(archive_path, mode="r:gz") as archive:
        for member in archive:
            pinned = expected.get(member.name)
            if pinned is None:
                continue
            if member.name in seen or not member.isfile() or member.size != pinned.get("bytes"):
                raise ValueError(f"YCB archive member identity/type/size mismatch: {member.name}")
            source = archive.extractfile(member)
            if source is None:
                raise ValueError(f"YCB archive member cannot be read: {member.name}")
            digest = hashlib.sha256()
            size = 0
            with source:
                for chunk in iter(lambda: source.read(1024 * 1024), b""):
                    digest.update(chunk)
                    size += len(chunk)
            if size != pinned.get("bytes") or digest.hexdigest() != pinned.get("sha256"):
                raise ValueError(
                    f"YCB extracted record is not bound to its archive member: {member.name}"
                )
            seen.add(member.name)
    missing = set(expected) - seen
    if missing:
        raise ValueError(f"YCB archive is missing recorded member: {sorted(missing)[0]}")


def validate_ycb_manifest(manifest_path: Path) -> dict:
    manifest_path = Path(manifest_path).absolute()
    if len(manifest_path.parents) < 3:
        raise ValueError("YCB manifest path is not under the dataset root")
    root = manifest_path.parents[2]
    manifest_relative = manifest_path.relative_to(root).as_posix()
    for candidate in (manifest_path, *manifest_path.parents):
        if candidate == root.parent:
            break
        if candidate.is_symlink() or (
            hasattr(candidate, "is_junction") and candidate.is_junction()
        ):
            raise ValueError("YCB manifest path may not traverse a symlink or junction")
    root = root.resolve(strict=True)
    manifest_path = _regular_file(root, manifest_relative)
    document = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (
        document.get("dataset_id") != DATASET_ID
        or document.get("redistributable") is not False
        or document.get("physical_measurements_present") is not False
    ):
        raise ValueError("YCB private-reference manifest identity/authority flags are invalid")
    for collection in (document.get("models"), [document.get("photos")]):
        for source in collection:
            if (
                source.get("license_id") != "CC-BY-4.0"
                or source.get("license_url") != YCB_LICENSE_URL
                or not source.get("attribution_detail")
                or not source.get("source_archive_sha256")
            ):
                raise ValueError("YCB license, attribution or archive provenance is missing")
            archive_name = source.get("source_archive")
            if (
                type(archive_name) is not str
                or Path(archive_name).name != archive_name
                or not re.fullmatch(r"[a-zA-Z0-9_.-]+\.tgz", archive_name)
            ):
                raise ValueError("unsafe YCB archive identity")
            pinned = YCB_ARCHIVE_IDENTITIES.get(archive_name)
            if (
                source.get("source_index_url") != YCB_INDEX_URL
                or pinned is None
                or source.get("source_url") != pinned["url"]
            ):
                raise ValueError(
                    f"YCB source URL does not bind to the official archive: {archive_name}"
                )
            archive = _regular_file(root, f"source/ycb/{archive_name}", max_bytes=2_000_000_000)
            if (
                type(source.get("source_archive_bytes")) is not int
                or source["source_archive_bytes"] != pinned["bytes"]
                or archive.stat().st_size != pinned["bytes"]
                or source.get("source_archive_sha256") != pinned["sha256"]
                or _sha256(archive) != pinned["sha256"]
            ):
                raise ValueError(f"source archive length/hash mismatch: {archive_name}")
    model_objects = {source.get("object_id") for source in document["models"]}
    if model_objects != {"006_mustard_bottle", "021_bleach_cleanser"}:
        raise ValueError("required YCB real package model references are missing")
    model_count = image_count = total_bytes = 0
    for source in document["models"]:
        if "not independently verified physical dimensional ground truth" not in source.get(
            "capture_scale_note", ""
        ):
            raise ValueError("YCB scanner scale must not be represented as physical ground truth")
        for record in source.get("records", []):
            _check_file(root, record)
            model_count += 1
        archive = _regular_file(
            root, f"source/ycb/{source['source_archive']}", max_bytes=2_000_000_000
        )
        _verify_archive_members(archive, source.get("records", []), "archive_member")
    photos = document["photos"]
    if photos.get("selection", {}).get(
        "frames_per_camera_max"
    ) != 6 or "pixel bytes preserved" not in photos.get("selection", {}).get(
        "modification_notice", ""
    ):
        raise ValueError("YCB photo subset notice or selection policy is missing")
    for record in photos.get("records", []):
        if (
            record.get("capture_type") != "real YCB Berkeley RGB photograph"
            or record.get("camera_pose_and_calibration")
            != "not provided/bound to this image by this package; unknown"
        ):
            raise ValueError("real photo provenance/camera uncertainty is missing")
        path = _regular_file(root, record.get("path", ""))
        with path.open("rb") as stream:
            if stream.read(3) != b"\xff\xd8\xff":
                raise ValueError(f"invalid JPEG signature: {record['path']}")
        _check_file(root, record)
        image_count += 1
    photo_archive = _regular_file(
        root, f"source/ycb/{photos['source_archive']}", max_bytes=2_000_000_000
    )
    _verify_archive_members(photo_archive, photos.get("records", []), "ycb_archive_member")
    if len(model_objects) != 2 or image_count != 30 or model_count < 8:
        raise ValueError("YCB subset size is outside the intended bounded package")
    total_bytes = sum(
        record["bytes"] for source in document["models"] for record in source["records"]
    ) + sum(record["bytes"] for record in photos["records"])
    return {
        "dataset_id": DATASET_ID,
        "licensed_model_objects": len(model_objects),
        "real_photos": image_count,
        "model_files": model_count,
        "derived_bytes": total_bytes,
        "manifest_sha256": _sha256(manifest_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    print(json.dumps(validate_ycb_manifest(args.manifest), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
