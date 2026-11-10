"""Safely extract a bounded, attributed subset from official YCB archives."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import tarfile
import tempfile
from collections import defaultdict
from pathlib import Path, PurePosixPath, PureWindowsPath

if __package__:
    from tools.datasets.dataset_root import resolve_dataset_root
    from tools.datasets.ycb_source_identity import YCB_ARCHIVE_IDENTITIES, YCB_INDEX_URL
else:
    from dataset_root import resolve_dataset_root
    from ycb_source_identity import YCB_ARCHIVE_IDENTITIES, YCB_INDEX_URL


ATTRIBUTION = "Calli, Singh, Walsman, Srinivasa, Abbeel, and Dollar; YCB Object and Model Set"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _archive_url(archive_path: Path) -> str:
    try:
        return YCB_ARCHIVE_IDENTITIES[archive_path.name]["url"]
    except KeyError as exc:
        raise ValueError(f"archive is not in the verified YCB source allowlist: {archive_path.name}") from exc


def _verified_archive(archive_path: Path, dataset_root: Path) -> tuple[Path, dict[str, object]]:
    identity = YCB_ARCHIVE_IDENTITIES.get(archive_path.name)
    if identity is None:
        raise ValueError("archive is not in the verified YCB source allowlist")
    root = dataset_root.resolve(strict=True)
    _reject_reparse_points(archive_path, root)
    try:
        resolved = archive_path.resolve(strict=True)
        resolved.relative_to(root)
    except (OSError, ValueError) as error:
        raise ValueError("YCB archive is missing or outside the local dataset root") from error
    metadata = resolved.stat()
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_size != identity["bytes"]:
        raise ValueError("YCB archive is not the pinned regular file/byte length")
    if sha256(resolved) != identity["sha256"]:
        raise ValueError("YCB archive SHA-256 differs from the pinned official source")
    return resolved, identity


def _safe_name(name: str) -> PurePosixPath:
    if not name or "\x00" in name or "\\" in name or ":" in name:
        raise ValueError(f"unsafe cross-platform archive member path: {name!r}")
    path = PurePosixPath(name)
    if PureWindowsPath(name).is_absolute() or PureWindowsPath(name).drive or path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError(f"unsafe archive member path: {name!r}")
    return path


def _reject_reparse_points(path: Path, boundary: Path) -> None:
    boundary = boundary.resolve()
    current = path
    try:
        current.relative_to(boundary)
    except ValueError as exc:
        raise ValueError(f"destination escapes dataset root: {path}") from exc
    while current != boundary:
        if current.is_symlink() or (hasattr(current, "is_junction") and current.is_junction()):
            raise ValueError(f"destination traverses a symlink or junction: {current}")
        current = current.parent
    if boundary.is_symlink() or (hasattr(boundary, "is_junction") and boundary.is_junction()):
        raise ValueError("dataset boundary may not be a symlink or junction")


def _resolve_dataset_root(requested: Path, localappdata: Path) -> Path:
    return resolve_dataset_root(requested, localappdata)


def _prepare_destination(dataset_root: Path, output_root: Path, member_path: PurePosixPath) -> Path:
    dataset_root = dataset_root.resolve(strict=True)
    try:
        relative_root = output_root.relative_to(dataset_root)
    except ValueError as exc:
        raise ValueError("extraction destination must stay within the dataset root") from exc
    _reject_reparse_points(dataset_root, dataset_root.parent)
    current = dataset_root
    for component in relative_root.parts:
        current = current / component
        if current.exists():
            if not current.is_dir():
                raise ValueError(f"archive destination parent is not a directory: {current}")
        else:
            current.mkdir()
        _reject_reparse_points(current, dataset_root)
    for part in member_path.parts[:-1]:
        current = current / part
        if current.exists():
            if not current.is_dir():
                raise ValueError(f"archive destination parent is not a directory: {current}")
        else:
            current.mkdir()
        _reject_reparse_points(current, dataset_root)
    destination = current / member_path.parts[-1]
    _reject_reparse_points(destination, dataset_root)
    return destination


def _copy_or_verify(
    src, destination: Path, expected_size: int, dataset_root: Path
) -> tuple[int, str]:
    digest = hashlib.sha256()
    written = 0
    _reject_reparse_points(destination, dataset_root.resolve(strict=True))
    if destination.exists():
        if destination.is_symlink() or not destination.is_file():
            raise ValueError(f"existing destination is not a regular file: {destination}")
        for chunk in iter(lambda: src.read(1024 * 1024), b""):
            digest.update(chunk)
            written += len(chunk)
        calculated = digest.hexdigest()
        if written != expected_size or destination.stat().st_size != expected_size or sha256(destination) != calculated:
            raise ValueError(f"existing extraction differs from source archive: {destination}")
        return written, calculated
    fd, temporary_name = tempfile.mkstemp(prefix=".ycb-extract-", suffix=".tmp", dir=destination.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "wb") as dst:
            for chunk in iter(lambda: src.read(1024 * 1024), b""):
                dst.write(chunk)
                digest.update(chunk)
                written += len(chunk)
            dst.flush()
            os.fsync(dst.fileno())
        if written != expected_size:
            raise ValueError(f"source member size mismatch: {destination}")
        calculated = digest.hexdigest()
        try:
            os.link(temporary, destination)
        except FileExistsError:
            _reject_reparse_points(destination, dataset_root.resolve(strict=True))
            if not destination.is_file() or destination.stat().st_size != expected_size or sha256(destination) != calculated:
                raise ValueError(f"existing extraction differs from source archive: {destination}")
        return written, calculated
    finally:
        temporary.unlink(missing_ok=True)


def selected_rgb_members(archive: tarfile.TarFile, per_camera: int = 6) -> list[str]:
    candidates: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for member in archive.getmembers():
        name = _safe_name(member.name)
        if not member.isfile() or len(name.parts) != 2 or name.suffix.lower() not in {".jpg", ".jpeg"}:
            continue
        match = re.fullmatch(r"N(\d+)_(\d+)", name.stem)
        if match:
            candidates[match.group(1)].append((int(match.group(2)), member.name))
    selected = []
    for camera_id in sorted(candidates, key=int):
        frames = sorted(candidates[camera_id])
        if not frames:
            continue
        indexes = {round(i * (len(frames) - 1) / (per_camera - 1)) for i in range(per_camera)} if per_camera > 1 else {len(frames) // 2}
        selected.extend(name for i, (_, name) in enumerate(frames) if i in indexes)
    if not selected:
        raise ValueError("no YCB RGB frames matched the expected N<camera>_<frame>.jpg shape")
    return selected


def extract_rgb(archive_path: Path, output: Path, dataset_root: Path, per_camera: int = 6) -> dict:
    archive_path, archive_identity = _verified_archive(archive_path, dataset_root)
    source_hash = str(archive_identity["sha256"])
    with tarfile.open(archive_path, mode="r:gz") as archive:
        selected = set(selected_rgb_members(archive, per_camera))
        records = []
        for member in archive:
            if member.name not in selected:
                continue
            rel = _safe_name(member.name)
            if member.size > 100 * 1024 * 1024:
                raise ValueError(f"selected YCB frame exceeds the per-file size cap: {member.name}")
            destination = _prepare_destination(dataset_root, output, rel)
            src = archive.extractfile(member)
            if src is None:
                raise ValueError(f"member did not contain a regular file: {member.name}")
            with src:
                source_bytes, source_digest = _copy_or_verify(src, destination, member.size, dataset_root)
            camera_group = re.fullmatch(r"N(\d+)_\d+", Path(member.name).stem).group(1)
            records.append({"path": destination.relative_to(dataset_root).as_posix(), "bytes": source_bytes, "sha256": source_digest, "format": "JPEG", "ycb_archive_member": member.name, "capture_type": "real YCB Berkeley RGB photograph", "camera_group": f"N{camera_group}", "camera_pose_and_calibration": "not provided/bound to this image by this package; unknown", "dimension_ground_truth": "not bound to this photo; no metric claim", "alteration_notice": "source JPEG bytes preserved; selected as a subset; no pixel alteration"})
    return {"source_url": _archive_url(archive_path), "source_index_url": YCB_INDEX_URL, "source_archive": archive_path.name, "source_archive_bytes": archive_path.stat().st_size, "source_archive_sha256": source_hash, "license": "CC BY 4.0", "license_id": "CC-BY-4.0", "license_url": "https://creativecommons.org/licenses/by/4.0/", "attribution": ATTRIBUTION, "attribution_detail": "The YCB Object and Model Set by Berk C. Calli, Arjun Singh, Aaron Walsman, Siddhartha Srinivasa, Pieter Abbeel, and Aaron M. Dollar.", "local_use": "private local PackLab software-validation copy; upstream CC BY 4.0 remains authoritative", "selection": {"method": "evenly sampled frame indices per available YCB N-camera group", "frames_per_camera_max": per_camera, "modification_notice": "selected 30 images from the source archive; pixel bytes preserved"}, "records": records}


def extract_model(archive_path: Path, output: Path, dataset_root: Path, object_id: str) -> dict:
    archive_path, archive_identity = _verified_archive(archive_path, dataset_root)
    source_hash = str(archive_identity["sha256"])
    prefix = f"{object_id}/google_16k/"
    allowed_suffixes = {".ply", ".stl", ".png", ".dae", ".xml"}
    records = []
    with tarfile.open(archive_path, mode="r:gz") as archive:
        for member in archive:
            if not member.isfile() or not member.name.startswith(prefix):
                continue
            rel = _safe_name(member.name)
            if rel.suffix.lower() not in allowed_suffixes or member.size > 100 * 1024 * 1024:
                continue
            destination = _prepare_destination(dataset_root, output, rel)
            src = archive.extractfile(member)
            if src is None:
                raise ValueError(f"member did not contain a regular file: {member.name}")
            with src:
                source_bytes, source_digest = _copy_or_verify(src, destination, member.size, dataset_root)
            records.append({"path": destination.relative_to(dataset_root).as_posix(), "bytes": source_bytes, "sha256": source_digest, "archive_member": member.name, "type": "YCB Google-scanner 16k object model/texture/metadata"})
    if not any(record["path"].endswith("textured.ply") for record in records):
        raise ValueError(f"expected textured.ply absent for {object_id}")
    return {"source_url": _archive_url(archive_path), "source_index_url": YCB_INDEX_URL, "source_archive": archive_path.name, "source_archive_bytes": archive_path.stat().st_size, "source_archive_sha256": source_hash, "license": "CC BY 4.0", "license_id": "CC-BY-4.0", "license_url": "https://creativecommons.org/licenses/by/4.0/", "attribution": ATTRIBUTION, "attribution_detail": "The YCB Object and Model Set by Berk C. Calli, Arjun Singh, Aaron Walsman, Siddhartha Srinivasa, Pieter Abbeel, and Aaron M. Dollar.", "modification_notice": "selected 16k Google-scanner package model/texture files from the source archive; file bytes preserved", "object_id": object_id, "capture_scale_note": "model scanner scale is source-provided model geometry; not independently verified physical dimensional ground truth", "records": records}


def _write_manifest(path: Path, dataset_root: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _reject_reparse_points(path.parent, dataset_root.resolve(strict=True))
    if path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()):
        raise ValueError("refusing to write the YCB manifest through a link")
    if path.exists():
        if not stat.S_ISREG(path.stat().st_mode):
            raise FileExistsError("refusing to replace a non-regular YCB manifest")
        prior = json.loads(path.read_text(encoding="utf-8"))
        if prior.get("dataset_id") != "packlab-m17-ycb-real-reference-v1":
            raise FileExistsError(f"refusing to replace an unrelated file: {path}")
    fd, temporary_name = tempfile.mkstemp(prefix=".manifest-", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True, help="outside-Git dataset root")
    args = parser.parse_args()
    try:
        root = _resolve_dataset_root(args.root, Path(os.environ["LOCALAPPDATA"]))
    except (KeyError, OSError, ValueError) as error:
        parser.error(str(error))
    _reject_reparse_points(root, root.parent)
    source = root / "source" / "ycb"
    derived = root / "derived" / "ycb"
    models = []
    for object_id, archive_name in [("006_mustard_bottle", "006_mustard_bottle_google_16k.tgz"), ("021_bleach_cleanser", "021_bleach_cleanser_google_16k.tgz")]:
        models.append(extract_model(source / archive_name, derived / "models", root, object_id))
    photos = extract_rgb(source / "006_mustard_bottle_berkeley_rgb_highres.tgz", derived / "photos", root, 6)
    document = {"schema_version": "1.0", "dataset_id": "packlab-m17-ycb-real-reference-v1", "physical_measurements_present": False, "redistributable": False, "notes": ["CC BY 4.0 applies to copyright/database rights held by licensors; it does not grant trademark/product-trade-dress rights.", "YCB RGB photographs and Google-scanner models are separate captures and are not registered image/model pairs here.", "No calibrated camera pose, scale verification, or physical measurement is claimed for extracted photo frames."], "models": models, "photos": photos}
    path = derived / "manifest.json"
    payload = json.dumps(document, indent=2, sort_keys=True) + "\n"
    _write_manifest(path, root, payload)
    print(json.dumps({"manifest": str(path), "models": len(models), "photos": len(photos["records"]), "manifest_sha256": sha256(path)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
