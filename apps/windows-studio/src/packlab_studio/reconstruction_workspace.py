"""Retry-safe, project-scoped reconstruction workspace authority."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import tempfile
import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from functools import cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError

from packlab_core.packscan import PackScanError, PackScanReport, read_packscan
from packlab_core.reconstruction import (
    CAMERA_PRIOR_POLICY_VERSION,
    PACKSCAN_INTRINSICS_CONVENTION,
    PACKSCAN_PIXEL_ORIGIN,
    PACKSCAN_POSE_CONVENTION,
    CameraPrior,
    CameraPriorAssessment,
    CameraPriorUse,
    ReconstructionInputSet,
)
from packlab_core.resource_paths import packlab_data_root

from .project_layout import ProjectLayout, ProjectLayoutError, safe_relative_path
from .provenance import ArtifactRecord, ProvenanceManager


class ReconstructionWorkspaceError(RuntimeError):
    pass


class WorkspaceState(StrEnum):
    ACTIVE = "active"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class ReconstructionWorkspace:
    project_id: str
    project_revision: int
    revision_id: str
    source_asset_id: str
    source_digest: str
    path: Path
    state: WorkspaceState

    @property
    def relative_path(self) -> str:
        return f"working/reconstruction/{self.revision_id}"


@dataclass(frozen=True, slots=True)
class WorkingSetImage:
    """One immutable PackScan image and its byte-preserving working copy."""

    order: int
    source_asset_id: str
    source_sha256: str
    working_asset_id: str
    working_sha256: str

    def as_dict(self) -> dict[str, object]:
        return {
            "order": self.order,
            "source_asset_id": self.source_asset_id,
            "source_sha256": self.source_sha256,
            "working_asset_id": self.working_asset_id,
            "working_sha256": self.working_sha256,
        }


@dataclass(frozen=True, slots=True)
class ReconstructionWorkingSet:
    """Published, revision-scoped inputs for a reconstruction backend."""

    workspace: ReconstructionWorkspace
    preprocessing_policy: str
    preprocessing_version: str
    images: tuple[WorkingSetImage, ...]
    inputs: ReconstructionInputSet
    manifest_path: Path


WORKING_SET_SCHEMA_VERSION = 1
WORKING_SET_PREPROCESSING_POLICY = "byte-preserving-copy"
WORKING_SET_PREPROCESSING_VERSION = "1"


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _atomic_json(target: Path, value: object) -> None:
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}-", suffix=".tmp", dir=target.parent
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, sort_keys=True, separators=(",", ":"))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, target)
    finally:
        Path(temporary_name).unlink(missing_ok=True)


def _atomic_bytes(target: Path, value: bytes) -> None:
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}-", suffix=".tmp", dir=target.parent
    )
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, target)
    finally:
        Path(temporary_name).unlink(missing_ok=True)


@cache
def _packscan_schema_validator(schema_name: str) -> Draft202012Validator:
    schema_path = packlab_data_root() / "schemas" / "packscan" / schema_name
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
    except (OSError, json.JSONDecodeError, SchemaError) as error:
        raise ReconstructionWorkspaceError(
            f"PackScan schema resource is unavailable: {schema_name}"
        ) from error
    return Draft202012Validator(schema, format_checker=FormatChecker())


def _validate_packscan_metadata(value: object, schema_name: str, path: str) -> None:
    errors = sorted(
        _packscan_schema_validator(schema_name).iter_errors(value),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        location = "/".join(str(part) for part in errors[0].absolute_path)
        suffix = f" at {location}" if location else ""
        raise ReconstructionWorkspaceError(f"PackScan metadata is invalid: {path}{suffix}")


def _json_object(data: bytes, path: str) -> dict[str, object]:
    try:
        value = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ReconstructionWorkspaceError(f"PackScan metadata JSON is invalid: {path}") from error
    if not isinstance(value, dict):
        raise ReconstructionWorkspaceError(f"PackScan metadata must be an object: {path}")
    return value


def _flatten_matrix(value: object, *, size: int, path: str) -> tuple[float, ...]:
    if not isinstance(value, list) or len(value) != size:
        raise ReconstructionWorkspaceError(f"PackScan matrix shape is invalid: {path}")
    rows: list[tuple[float, ...]] = []
    for row in value:
        if (
            not isinstance(row, list)
            or len(row) != size
            or not all(
                isinstance(number, (int, float))
                and not isinstance(number, bool)
                and math.isfinite(number)
                for number in row
            )
        ):
            raise ReconstructionWorkspaceError(f"PackScan matrix values are invalid: {path}")
        rows.append(tuple(float(number) for number in row))
    return tuple(number for row in rows for number in row)


def _same_matrix_product(left: tuple[float, ...], right: tuple[float, ...]) -> bool:
    product = tuple(
        sum(left[row * 4 + index] * right[index * 4 + column] for index in range(4))
        for row in range(4)
        for column in range(4)
    )
    return all(
        math.isclose(product[index], 1.0 if index % 5 == 0 else 0.0, rel_tol=0.0, abs_tol=1e-6)
        for index in range(16)
    )


def _is_rigid_camera_pose(matrix: tuple[float, ...]) -> bool:
    rotation = matrix
    for row in range(3):
        for column in range(3):
            dot = sum(rotation[row * 4 + axis] * rotation[column * 4 + axis] for axis in range(3))
            if not math.isclose(dot, 1.0 if row == column else 0.0, rel_tol=0.0, abs_tol=1e-6):
                return False
    determinant = (
        rotation[0] * (rotation[5] * rotation[10] - rotation[6] * rotation[9])
        - rotation[1] * (rotation[4] * rotation[10] - rotation[6] * rotation[8])
        + rotation[2] * (rotation[4] * rotation[9] - rotation[5] * rotation[8])
    )
    return math.isclose(determinant, 1.0, rel_tol=0.0, abs_tol=1e-6)


def _payload_kind(path: str) -> str | None:
    normalized = path.lower().replace("\\", "/")
    if not normalized.endswith(".json") or normalized == "metadata/photos.json":
        return None
    parts = normalized[:-5].split("/")
    if any("intrinsic" in part for part in parts):
        return "intrinsics"
    if any(part in {"pose", "poses"} or "pose" in part for part in parts):
        return "pose"
    return None


def _payload_photo_id(
    path: str, photo_ids: tuple[str, ...], image_paths: tuple[str, ...]
) -> str | None:
    normalized = path.lower().replace("\\", "/")
    filename = normalized.rsplit("/", 1)[-1][:-5]
    candidates: list[str] = []
    for photo_id in photo_ids:
        lowered = photo_id.lower()
        if lowered in normalized.split("/") or filename == lowered:
            candidates.append(photo_id)
            continue
        suffixes = (
            ".intrinsics",
            ".intrinsic",
            ".pose",
            "_intrinsics",
            "_pose",
            "-intrinsics",
            "-pose",
        )
        if any(filename == lowered + suffix for suffix in suffixes):
            candidates.append(photo_id)
    for image_path in image_paths:
        image_name = image_path.rsplit("/", 1)[-1]
        image_stem = image_name.rsplit(".", 1)[0].lower()
        if filename == image_stem:
            matching = [photo_id for photo_id in photo_ids if photo_id.lower() in normalized]
            candidates.extend(matching)
    unique = tuple(dict.fromkeys(candidates))
    if len(unique) == 1:
        return unique[0]
    return None


class ReconstructionWorkspaceManager:
    def __init__(self, layout: ProjectLayout, provenance: ProvenanceManager | None = None) -> None:
        self.layout = layout
        self.provenance = provenance or ProvenanceManager(layout)

    def create(
        self,
        *,
        project_id: str,
        project_revision: int,
        source_asset_id: str,
        source_digest: str,
        revision_id: str | None = None,
    ) -> ReconstructionWorkspace:
        source = self._source_path(source_asset_id)
        if not re.fullmatch(r"[0-9a-f]{64}", source_digest):
            raise ReconstructionWorkspaceError("source digest is invalid")
        if not source.is_file():
            raise ReconstructionWorkspaceError("RAW_CAPTURE source is missing")
        if _digest(source) != source_digest:
            raise ReconstructionWorkspaceError("RAW_CAPTURE source digest does not match")
        revision = revision_id or f"r-{uuid.uuid4().hex}"
        if not re.fullmatch(r"[A-Za-z0-9_-]+", revision):
            raise ReconstructionWorkspaceError("reconstruction revision is unsafe")
        path = self.layout.path("working", Path("reconstruction") / revision)
        if path.exists():
            raise ReconstructionWorkspaceError("reconstruction revision already exists")
        (path / "inputs").mkdir(parents=True)
        (path / "outputs").mkdir()
        (path / "logs").mkdir()
        workspace = ReconstructionWorkspace(
            project_id,
            project_revision,
            revision,
            source_asset_id,
            source_digest,
            path,
            WorkspaceState.ACTIVE,
        )
        self._write_manifest(workspace)
        return workspace

    def copy_raw_input(self, workspace: ReconstructionWorkspace, destination: str) -> str:
        self._ensure_active(workspace)
        destination_path = safe_relative_path(destination)
        source = self._source_path(workspace.source_asset_id)
        if not self.source_is_intact(workspace):
            raise ReconstructionWorkspaceError("RAW_CAPTURE source changed")
        target = workspace.path / "inputs" / destination_path
        target.parent.mkdir(parents=True, exist_ok=True)
        _atomic_bytes(target, source.read_bytes())
        return f"{workspace.relative_path}/inputs/{destination_path.as_posix()}"

    def materialize_working_set(
        self, workspace: ReconstructionWorkspace
    ) -> ReconstructionWorkingSet:
        """Validate RAW_CAPTURE and publish deterministic, byte-preserving inputs.

        PackScan validation happens before any working input is written. Files are
        staged as atomic individual copies and the existing workspace manifest is
        published last, so a failed preparation cannot advertise a working set.
        """

        self._ensure_active(workspace)
        source = self._source_path(workspace.source_asset_id)
        if not self.source_is_intact(workspace):
            raise ReconstructionWorkspaceError("RAW_CAPTURE source changed")
        try:
            report = read_packscan(source)
        except PackScanError as error:
            raise ReconstructionWorkspaceError(
                f"RAW_CAPTURE PackScan validation failed: {error.code}"
            ) from error

        manifest = self._read_workspace_manifest(workspace)
        if manifest.get("working_set") is not None:
            raise ReconstructionWorkspaceError("working set is already published")

        image_paths = self._declared_image_paths(report)
        input_root = workspace.path / "inputs"
        self._ensure_empty_input_root(input_root)
        targets: list[tuple[str, Path, bytes]] = []
        seen_targets: set[str] = set()
        images: list[WorkingSetImage] = []
        for order, source_asset_id in enumerate(image_paths):
            data = report.payloads.get(source_asset_id)
            if data is None:
                raise ReconstructionWorkspaceError(
                    f"RAW_CAPTURE declared image is missing: {source_asset_id}"
                )
            try:
                relative = safe_relative_path(source_asset_id)
            except ProjectLayoutError as error:
                raise ReconstructionWorkspaceError(
                    f"working-set image path is unsafe: {source_asset_id}"
                ) from error
            working_asset_id = f"{workspace.relative_path}/inputs/{relative.as_posix()}"
            target = self._working_input_path(input_root, relative)
            target_key = target.relative_to(input_root).as_posix().casefold()
            if target_key in seen_targets or target.exists() or target.is_symlink():
                raise ReconstructionWorkspaceError(
                    f"working-set destination collision: {relative.as_posix()}"
                )
            seen_targets.add(target_key)
            digest = hashlib.sha256(data).hexdigest()
            targets.append((relative.as_posix(), target, data))
            images.append(
                WorkingSetImage(
                    order,
                    source_asset_id,
                    digest,
                    working_asset_id,
                    digest,
                )
            )

        if not images:
            raise ReconstructionWorkspaceError("RAW_CAPTURE contains no source images")
        inputs = ReconstructionInputSet(
            project_id=workspace.project_id,
            raw_capture_asset_id=workspace.source_asset_id,
            source_revision=workspace.revision_id,
            source_digest=workspace.source_digest,
            image_asset_ids=tuple(image.working_asset_id for image in images),
        )
        working_set = {
            "schema_version": WORKING_SET_SCHEMA_VERSION,
            "source_packscan_asset_id": workspace.source_asset_id,
            "source_packscan_sha256": workspace.source_digest,
            "preprocessing_policy": WORKING_SET_PREPROCESSING_POLICY,
            "preprocessing_version": WORKING_SET_PREPROCESSING_VERSION,
            "ordering": "lexicographic source asset ID",
            "images": [image.as_dict() for image in images],
            "reconstruction_input_set": inputs.as_dict(),
        }

        created: list[Path] = []
        try:
            for _relative, target, data in targets:
                target.parent.mkdir(parents=True, exist_ok=True)
                _atomic_bytes(target, data)
                created.append(target)
            self._write_manifest(workspace, working_set=working_set)
        except (OSError, ProjectLayoutError, ReconstructionWorkspaceError):
            for target in reversed(created):
                target.unlink(missing_ok=True)
            for directory in sorted(
                (path for path in input_root.rglob("*") if path.is_dir()),
                key=lambda path: len(path.parts),
                reverse=True,
            ):
                if directory != input_root:
                    directory.rmdir()
            raise

        return ReconstructionWorkingSet(
            workspace,
            WORKING_SET_PREPROCESSING_POLICY,
            WORKING_SET_PREPROCESSING_VERSION,
            tuple(images),
            inputs,
            workspace.path / "manifest.json",
        )

    def import_camera_priors(
        self,
        workspace: ReconstructionWorkspace,
        *,
        use: CameraPriorUse = CameraPriorUse.INITIALIZATION_ONLY,
        per_image_use: Mapping[str, CameraPriorUse] | None = None,
    ) -> CameraPriorAssessment:
        """Consume finalized PackScan camera metadata for a published working set.

        The importer is deliberately read-only. It revalidates the finalized
        PackScan, the published PL-0166 working-set identity, and every
        recognized metadata payload before returning priors bound to the exact
        revision-scoped working image IDs.
        """

        self._ensure_active(workspace)
        if not self.source_is_intact(workspace):
            raise ReconstructionWorkspaceError("RAW_CAPTURE source changed")
        try:
            default_use = CameraPriorUse(use)
        except (TypeError, ValueError) as error:
            raise ReconstructionWorkspaceError("camera prior use mode is invalid") from error
        try:
            report = read_packscan(self._source_path(workspace.source_asset_id))
        except PackScanError as error:
            raise ReconstructionWorkspaceError(
                f"RAW_CAPTURE PackScan validation failed: {error.code}"
            ) from error

        working_set = self._published_working_set(workspace)
        self._verify_working_set_identity(workspace, working_set, report)
        photos_by_image, photos_by_id = self._read_photo_metadata(report, working_set)
        candidates, candidate_warnings = self._find_prior_payloads(
            report, photos_by_id, photos_by_image
        )
        device = report.manifest.get("device")
        if not isinstance(device, dict):
            raise ReconstructionWorkspaceError("PackScan device metadata is invalid")

        requested_by_image = per_image_use or {}
        priors: list[CameraPrior] = []
        warnings = list(candidate_warnings)
        for image in working_set.images:
            photo = photos_by_image.get(image.source_asset_id)
            requested_use = requested_by_image.get(
                image.working_asset_id,
                requested_by_image.get(image.source_asset_id, default_use),
            )
            try:
                requested_use = CameraPriorUse(requested_use)
            except (TypeError, ValueError) as error:
                raise ReconstructionWorkspaceError("camera prior use mode is invalid") from error
            if photo is None:
                prior = CameraPrior.missing(
                    image.working_asset_id,
                    "photo metadata does not bind the working image",
                )
            else:
                photo_id = photo.get("photo_id")
                width = photo.get("width")
                height = photo.get("height")
                if (
                    not isinstance(photo_id, str)
                    or not isinstance(width, int)
                    or not isinstance(height, int)
                ):
                    raise ReconstructionWorkspaceError("PackScan photo metadata is invalid")
                intrinsic_path = candidates.get(("intrinsics", photo_id))
                pose_path = candidates.get(("pose", photo_id))
                try:
                    prior = self._build_camera_prior(
                        workspace,
                        image,
                        {**photo, "width": width, "height": height},
                        device,
                        report,
                        intrinsic_path,
                        pose_path,
                        requested_use,
                    )
                except ReconstructionWorkspaceError as error:
                    prior = CameraPrior(
                        image.working_asset_id,
                        width=width,
                        height=height,
                        use=CameraPriorUse.REJECTED,
                        reason=str(error),
                        source_image_asset_id=image.source_asset_id,
                        source_digest=workspace.source_digest,
                        source_revision=workspace.revision_id,
                        policy_version=CAMERA_PRIOR_POLICY_VERSION,
                    )
            if prior.use is CameraPriorUse.REJECTED:
                warnings.append(f"camera prior rejected: {image.working_asset_id} ({prior.reason})")
            priors.append(prior)
        return CameraPriorAssessment(tuple(priors), tuple(warnings))

    def _published_working_set(
        self, workspace: ReconstructionWorkspace
    ) -> ReconstructionWorkingSet:
        manifest = self._read_workspace_manifest(workspace)
        value = manifest.get("working_set")
        if not isinstance(value, dict):
            raise ReconstructionWorkspaceError("working set is not published")
        try:
            raw_images = value["images"]
            raw_inputs = value["reconstruction_input_set"]
            if not isinstance(raw_images, list) or not isinstance(raw_inputs, dict):
                raise TypeError
            images = tuple(
                WorkingSetImage(
                    int(item["order"]),
                    str(item["source_asset_id"]),
                    str(item["source_sha256"]),
                    str(item["working_asset_id"]),
                    str(item["working_sha256"]),
                )
                for item in raw_images
                if isinstance(item, dict)
            )
            if len(images) != len(raw_images):
                raise TypeError
            inputs = ReconstructionInputSet(
                str(raw_inputs["project_id"]),
                str(raw_inputs["raw_capture_asset_id"]),
                str(raw_inputs["source_revision"]),
                str(raw_inputs["source_digest"]),
                tuple(str(image) for image in raw_inputs["image_asset_ids"]),
            )
            policy = str(value["preprocessing_policy"])
            version = str(value["preprocessing_version"])
        except (KeyError, TypeError, ValueError) as error:
            raise ReconstructionWorkspaceError("working-set manifest is invalid") from error
        return ReconstructionWorkingSet(
            workspace,
            policy,
            version,
            images,
            inputs,
            workspace.path / "manifest.json",
        )

    def _verify_working_set_identity(
        self,
        workspace: ReconstructionWorkspace,
        working_set: ReconstructionWorkingSet,
        report: PackScanReport,
    ) -> None:
        if (
            working_set.workspace.revision_id != workspace.revision_id
            or working_set.inputs.project_id != workspace.project_id
            or working_set.inputs.raw_capture_asset_id != workspace.source_asset_id
            or working_set.inputs.source_revision != workspace.revision_id
            or working_set.inputs.source_digest != workspace.source_digest
            or working_set.workspace.source_digest != workspace.source_digest
        ):
            raise ReconstructionWorkspaceError("working-set revision or source binding changed")
        declared_images = self._declared_image_paths(report)
        if tuple(image.source_asset_id for image in working_set.images) != declared_images:
            raise ReconstructionWorkspaceError("working-set image identity does not match PackScan")
        if working_set.inputs.image_asset_ids != tuple(
            image.working_asset_id for image in working_set.images
        ):
            raise ReconstructionWorkspaceError("working-set input image IDs are inconsistent")
        for order, image in enumerate(working_set.images):
            if image.order != order:
                raise ReconstructionWorkspaceError("working-set image ordering is invalid")
            source_bytes = report.payloads.get(image.source_asset_id)
            if (
                source_bytes is None
                or hashlib.sha256(source_bytes).hexdigest() != image.source_sha256
            ):
                raise ReconstructionWorkspaceError("working-set source image digest changed")
            expected = workspace.path / "inputs" / safe_relative_path(image.source_asset_id)
            if (
                image.working_asset_id
                != f"{workspace.relative_path}/inputs/{safe_relative_path(image.source_asset_id).as_posix()}"
            ):
                raise ReconstructionWorkspaceError("working-set working image ID is inconsistent")
            if expected.is_symlink() or not expected.is_file():
                raise ReconstructionWorkspaceError("working-set image is missing or unsafe")
            if hashlib.sha256(expected.read_bytes()).hexdigest() != image.working_sha256:
                raise ReconstructionWorkspaceError("working-set image bytes changed")

    @staticmethod
    def _read_photo_metadata(
        report: PackScanReport, working_set: ReconstructionWorkingSet
    ) -> tuple[dict[str, dict[str, object]], dict[str, dict[str, object]]]:
        try:
            value = _json_object(report.payloads["metadata/photos.json"], "metadata/photos.json")
            _validate_packscan_metadata(value, "photo-metadata.schema.json", "metadata/photos.json")
        except KeyError as error:
            raise ReconstructionWorkspaceError("PackScan photo metadata is missing") from error
        photos = value.get("photos")
        if not isinstance(photos, list):
            raise ReconstructionWorkspaceError("PackScan photo metadata is invalid")
        by_image: dict[str, dict[str, object]] = {}
        by_id: dict[str, dict[str, object]] = {}
        for item in photos:
            if not isinstance(item, dict):
                raise ReconstructionWorkspaceError("PackScan photo metadata is invalid")
            image_path = item.get("image_path")
            photo_id = item.get("photo_id")
            dimensions = item.get("pixel_dimensions")
            if (
                not isinstance(image_path, str)
                or not isinstance(photo_id, str)
                or not isinstance(dimensions, dict)
            ):
                raise ReconstructionWorkspaceError("PackScan photo metadata is invalid")
            if image_path in by_image or photo_id in by_id:
                raise ReconstructionWorkspaceError("PackScan photo metadata identity is duplicated")
            if not isinstance(dimensions.get("width"), int) or not isinstance(
                dimensions.get("height"), int
            ):
                raise ReconstructionWorkspaceError("PackScan photo dimensions are invalid")
            by_image[image_path] = {
                "photo_id": photo_id,
                "width": dimensions["width"],
                "height": dimensions["height"],
            }
            by_id[photo_id] = by_image[image_path]
        source_ids = {image.source_asset_id for image in working_set.images}
        if set(by_image) != source_ids:
            raise ReconstructionWorkspaceError(
                "PackScan photo metadata does not match working images"
            )
        return by_image, by_id

    @staticmethod
    def _find_prior_payloads(
        report: PackScanReport,
        photos_by_id: Mapping[str, dict[str, object]],
        photos_by_image: Mapping[str, dict[str, object]],
    ) -> tuple[dict[tuple[str, str], str], list[str]]:
        image_paths = tuple(photos_by_image)
        photo_ids = tuple(photos_by_id)
        candidates: dict[tuple[str, str], str] = {}
        ambiguous: set[tuple[str, str]] = set()
        warnings: list[str] = []
        payloads = report.manifest.get("payloads", ())
        if not isinstance(payloads, list):
            raise ReconstructionWorkspaceError("PackScan payload declaration is invalid")
        for item in payloads:
            if not isinstance(item, dict):
                continue
            path = item.get("path")
            if not isinstance(path, str):
                continue
            kind = _payload_kind(path)
            if kind is None:
                continue
            photo_id = _payload_photo_id(path, photo_ids, image_paths)
            if photo_id is None:
                warnings.append(f"camera metadata payload has no unambiguous image binding: {path}")
                continue
            key = (kind, photo_id)
            if key in ambiguous:
                warnings.append(f"duplicate camera metadata payload rejected: {path}")
                continue
            if key in candidates:
                warnings.append(f"duplicate camera metadata payload rejected: {path}")
                candidates.pop(key)
                ambiguous.add(key)
                continue
            candidates[key] = path
        return candidates, warnings

    def _build_camera_prior(
        self,
        workspace: ReconstructionWorkspace,
        image: WorkingSetImage,
        photo: dict[str, object],
        device: dict[str, object],
        report: PackScanReport,
        intrinsic_path: str | None,
        pose_path: str | None,
        use: CameraPriorUse,
    ) -> CameraPrior:
        if intrinsic_path is None:
            raise ReconstructionWorkspaceError("camera intrinsics are unavailable for image")
        declaration = self._payload_declaration(report, intrinsic_path)
        if declaration.get("authority") != "source":
            raise ReconstructionWorkspaceError(
                "camera intrinsics are not authoritative source metadata"
            )
        intrinsic = _json_object(report.payloads[intrinsic_path], intrinsic_path)
        _validate_packscan_metadata(intrinsic, "camera-intrinsics.schema.json", intrinsic_path)
        lens = intrinsic.get("lens")
        provenance = intrinsic.get("provenance")
        if not isinstance(lens, dict) or not isinstance(provenance, dict):
            raise ReconstructionWorkspaceError("camera intrinsics provenance is incomplete")
        if lens.get("device_model") != device.get("model"):
            raise ReconstructionWorkspaceError(
                "camera intrinsics device model does not match PackScan"
            )
        manifest_lens = device.get("lens")
        if manifest_lens is not None and lens.get("lens_identity") != manifest_lens:
            raise ReconstructionWorkspaceError(
                "camera intrinsics lens identity does not match PackScan"
            )
        dimensions = photo["width"], photo["height"]
        matrix, distortion_model, distortion_coefficients = self._normalize_intrinsics(
            intrinsic, dimensions, intrinsic_path
        )

        pose: tuple[float, ...] | None = None
        pose_source: str | None = None
        camera_convention: str | None = None
        pose_unit: str | None = None
        reason = "capture metadata is a camera prior only; M09 owns metric scale"
        if pose_path is not None:
            pose_declaration = self._payload_declaration(report, pose_path)
            if pose_declaration.get("authority") != "source":
                raise ReconstructionWorkspaceError(
                    "capture pose is not authoritative source metadata"
                )
            pose_record = _json_object(report.payloads[pose_path], pose_path)
            _validate_packscan_metadata(pose_record, "pose.schema.json", pose_path)
            status = pose_record.get("status")
            pose_source_record = pose_record.get("provenance")
            if not isinstance(pose_source_record, dict):
                raise ReconstructionWorkspaceError("capture pose provenance is incomplete")
            pose_source = str(pose_source_record["source"])
            if status == "unavailable":
                reason = "capture pose unavailable; intrinsics remain a non-metrology prior"
            else:
                if status == "degraded" and use in {
                    CameraPriorUse.FIXED,
                    CameraPriorUse.REFINED,
                }:
                    raise ReconstructionWorkspaceError(
                        "degraded capture pose cannot be fixed or refined"
                    )
                camera_convention = str(pose_record["coordinate_convention"])
                pose_unit = str(pose_record["translation_unit"])
                pose = _flatten_matrix(
                    pose_record["camera_to_world_matrix"], size=4, path=pose_path
                )
                if pose[12:15] != (0.0, 0.0, 0.0) or pose[15] != 1:
                    raise ReconstructionWorkspaceError("capture pose homogeneous matrix is invalid")
                if not _is_rigid_camera_pose(pose):
                    raise ReconstructionWorkspaceError("capture pose rotation is invalid")
                world_to_camera_value = pose_record.get("world_to_camera_matrix")
                if world_to_camera_value is not None:
                    world_to_camera = _flatten_matrix(world_to_camera_value, size=4, path=pose_path)
                    if not _same_matrix_product(pose, world_to_camera) or not _same_matrix_product(
                        world_to_camera, pose
                    ):
                        raise ReconstructionWorkspaceError("capture pose matrices are inconsistent")
                quaternion = pose_record.get("camera_to_world_quaternion")
                if isinstance(quaternion, dict):
                    values = tuple(float(quaternion[key]) for key in ("x", "y", "z", "w"))
                    if not math.isclose(sum(value * value for value in values), 1.0, abs_tol=1e-3):
                        raise ReconstructionWorkspaceError(
                            "capture pose quaternion is not normalized"
                        )
        if use is CameraPriorUse.REJECTED:
            reason = "prior use was explicitly rejected by caller"
        width = photo.get("width")
        height = photo.get("height")
        if not isinstance(width, int) or not isinstance(height, int):
            raise ReconstructionWorkspaceError("PackScan photo dimensions are invalid")
        return CameraPrior(
            image.working_asset_id,
            width=width,
            height=height,
            intrinsics=matrix,
            pose=pose,
            use=use,
            reason=reason,
            source_image_asset_id=image.source_asset_id,
            source_digest=workspace.source_digest,
            source_revision=workspace.revision_id,
            source=str(provenance["source"]),
            pose_source=pose_source,
            lens_identity=str(lens["lens_identity"]),
            dimensions_unit="px",
            intrinsics_unit="px",
            intrinsics_convention=PACKSCAN_INTRINSICS_CONVENTION,
            pixel_coordinate_origin=PACKSCAN_PIXEL_ORIGIN,
            camera_convention=camera_convention,
            pose_convention=PACKSCAN_POSE_CONVENTION if pose is not None else None,
            pose_unit=pose_unit,
            policy_version=CAMERA_PRIOR_POLICY_VERSION,
            distortion_model=distortion_model,
            distortion_coefficients=distortion_coefficients,
        )

    @staticmethod
    def _payload_declaration(report: PackScanReport, path: str) -> dict[str, object]:
        payloads = report.manifest.get("payloads", ())
        if not isinstance(payloads, list):
            raise ReconstructionWorkspaceError("PackScan payload declaration is invalid")
        for item in payloads:
            if isinstance(item, dict) and item.get("path") == path:
                return item
        raise ReconstructionWorkspaceError(f"PackScan payload declaration is missing: {path}")

    @staticmethod
    def _normalize_intrinsics(
        record: dict[str, object], dimensions: tuple[object, object], path: str
    ) -> tuple[tuple[float, ...], str, tuple[float, ...]]:
        width, height = dimensions
        if not isinstance(width, int) or not isinstance(height, int) or width <= 0 or height <= 0:
            raise ReconstructionWorkspaceError("image dimensions are invalid")
        image_dimensions = (width, height)
        reference = record.get("reference_dimensions")
        target = record.get("target_dimensions")
        policy = record.get("dimension_policy")
        matrix = _flatten_matrix(record.get("intrinsic_matrix"), size=3, path=path)
        if matrix[6] != 0 or matrix[7] != 0 or matrix[8] != 1 or matrix[0] <= 0 or matrix[4] <= 0:
            raise ReconstructionWorkspaceError("camera intrinsics matrix is invalid")
        if not isinstance(reference, dict) or not isinstance(policy, str):
            raise ReconstructionWorkspaceError("camera intrinsics dimensions are incomplete")
        reference_dimensions = (reference.get("width"), reference.get("height"))
        if not all(isinstance(value, int) and value > 0 for value in reference_dimensions):
            raise ReconstructionWorkspaceError("camera intrinsics reference dimensions are invalid")
        reference_width, reference_height = reference_dimensions
        if not isinstance(reference_width, int) or not isinstance(reference_height, int):
            raise ReconstructionWorkspaceError("camera intrinsics reference dimensions are invalid")
        target_dimensions = None
        if target is not None:
            if not isinstance(target, dict):
                raise ReconstructionWorkspaceError(
                    "camera intrinsics target dimensions are invalid"
                )
            target_dimensions = (target.get("width"), target.get("height"))
            if not all(isinstance(value, int) and value > 0 for value in target_dimensions):
                raise ReconstructionWorkspaceError(
                    "camera intrinsics target dimensions are invalid"
                )
            if target_dimensions != image_dimensions:
                raise ReconstructionWorkspaceError(
                    "camera intrinsics target dimensions do not match image"
                )
        if policy == "exact_reference_only":
            if image_dimensions != reference_dimensions:
                raise ReconstructionWorkspaceError(
                    "camera intrinsics dimensions do not match reference"
                )
        elif policy == "uniform_scale_about_origin":
            if not math.isclose(
                width / reference_width,
                height / reference_height,
                rel_tol=0.0,
                abs_tol=1e-12,
            ):
                raise ReconstructionWorkspaceError("camera intrinsics aspect ratio changed")
            scale = width / reference_width
            matrix = tuple(
                value * scale if index in {0, 1, 2, 3, 4, 5} else value
                for index, value in enumerate(matrix)
            )
        else:
            raise ReconstructionWorkspaceError("camera intrinsics dimension policy is ambiguous")
        distortion = record.get("distortion")
        if not isinstance(distortion, dict):
            raise ReconstructionWorkspaceError("camera intrinsics distortion is incomplete")
        coefficients = distortion.get("coefficients")
        if not isinstance(coefficients, list) or not all(
            isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
            for value in coefficients
        ):
            raise ReconstructionWorkspaceError("camera intrinsics distortion values are invalid")
        return (
            matrix,
            str(distortion["model"]),
            tuple(float(value) for value in coefficients),
        )

    def write_output(
        self, workspace: ReconstructionWorkspace, relative_path: str, data: bytes
    ) -> Path:
        self._ensure_active(workspace)
        target = workspace.path / "outputs" / safe_relative_path(relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        _atomic_bytes(target, data)
        return target

    def complete(
        self, workspace: ReconstructionWorkspace, *, parameters: dict[str, Any] | None = None
    ) -> ArtifactRecord:
        self._ensure_active(workspace)
        if not self.source_is_intact(workspace):
            self.fail(workspace, "RAW_CAPTURE source changed")
            raise ReconstructionWorkspaceError("RAW_CAPTURE source changed")
        completed = ReconstructionWorkspace(
            workspace.project_id,
            workspace.project_revision,
            workspace.revision_id,
            workspace.source_asset_id,
            workspace.source_digest,
            workspace.path,
            WorkspaceState.SUCCEEDED,
        )
        self._write_manifest(completed, parameters=parameters)
        return self.provenance.register(
            f"reconstruction:{workspace.revision_id}",
            workspace.relative_path,
            input_digests={workspace.source_asset_id: workspace.source_digest},
            parameters={"reconstruction_revision": workspace.revision_id, **(parameters or {})},
            project_revision=workspace.project_revision,
        )

    def fail(self, workspace: ReconstructionWorkspace, reason: str) -> ReconstructionWorkspace:
        return self._finish(workspace, WorkspaceState.FAILED, reason)

    def cancel(
        self, workspace: ReconstructionWorkspace, reason: str = "cancelled"
    ) -> ReconstructionWorkspace:
        if workspace.state is WorkspaceState.CANCELLED:
            return workspace
        return self._finish(workspace, WorkspaceState.CANCELLED, reason)

    def source_is_intact(self, workspace: ReconstructionWorkspace) -> bool:
        source = self._source_path(workspace.source_asset_id)
        return source.is_file() and _digest(source) == workspace.source_digest

    def _finish(
        self, workspace: ReconstructionWorkspace, state: WorkspaceState, reason: str
    ) -> ReconstructionWorkspace:
        self._ensure_active(workspace)
        finished = ReconstructionWorkspace(
            workspace.project_id,
            workspace.project_revision,
            workspace.revision_id,
            workspace.source_asset_id,
            workspace.source_digest,
            workspace.path,
            state,
        )
        self._write_manifest(finished, reason=reason)
        return finished

    def _write_manifest(
        self,
        workspace: ReconstructionWorkspace,
        *,
        reason: str | None = None,
        parameters: dict[str, Any] | None = None,
        working_set: dict[str, object] | None = None,
    ) -> None:
        manifest = {
            "schema_version": 1,
            "project_id": workspace.project_id,
            "project_revision": workspace.project_revision,
            "reconstruction_revision": workspace.revision_id,
            "source_asset_id": workspace.source_asset_id,
            "source_digest": workspace.source_digest,
            "workspace": workspace.relative_path,
            "state": workspace.state.value,
            "reason": reason,
            "parameters": parameters or {},
        }
        if working_set is None:
            try:
                existing = json.loads(
                    (workspace.path / "manifest.json").read_text(encoding="utf-8")
                )
            except (OSError, ValueError):
                existing = None
            if isinstance(existing, dict) and "working_set" in existing:
                manifest["working_set"] = existing["working_set"]
        if working_set is not None:
            manifest["working_set"] = working_set
        _atomic_json(
            workspace.path / "manifest.json",
            manifest,
        )

    @staticmethod
    def _read_workspace_manifest(workspace: ReconstructionWorkspace) -> dict[str, object]:
        try:
            value = json.loads((workspace.path / "manifest.json").read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            raise ReconstructionWorkspaceError("workspace manifest is corrupt") from error
        if not isinstance(value, dict):
            raise ReconstructionWorkspaceError("workspace manifest is corrupt")
        return value

    @staticmethod
    def _declared_image_paths(report: PackScanReport) -> tuple[str, ...]:
        payloads = report.manifest.get("payloads")
        if not isinstance(payloads, list):
            raise ReconstructionWorkspaceError("PackScan payload declaration is invalid")
        paths: list[str] = []
        for item in payloads:
            if not isinstance(item, dict) or item.get("kind") != "image":
                continue
            path = item.get("path")
            if not isinstance(path, str) or not path.startswith("images/"):
                raise ReconstructionWorkspaceError("PackScan image declaration is invalid")
            paths.append(path)
        return tuple(sorted(paths))

    @staticmethod
    def _ensure_empty_input_root(input_root: Path) -> None:
        if input_root.is_symlink() or not input_root.is_dir():
            raise ReconstructionWorkspaceError("working-set input boundary is unsafe")
        if any(input_root.iterdir()):
            raise ReconstructionWorkspaceError("working-set destination collision")

    @staticmethod
    def _working_input_path(input_root: Path, relative: Path) -> Path:
        target = (input_root / relative).resolve(strict=False)
        root = input_root.resolve()
        if os.path.commonpath((str(root), str(target))) != str(root):
            raise ReconstructionWorkspaceError("working-set destination escapes inputs")
        current = input_root
        for part in relative.parts[:-1]:
            current = current / part
            if current.is_symlink():
                raise ReconstructionWorkspaceError("working-set destination uses a symlink")
        return target

    @staticmethod
    def _ensure_active(workspace: ReconstructionWorkspace) -> None:
        if workspace.state is not WorkspaceState.ACTIVE:
            raise ReconstructionWorkspaceError("workspace is already terminal")

    def _source_path(self, source_asset_id: str) -> Path:
        normalized = source_asset_id.replace("\\", "/")
        if not normalized.startswith("raw/"):
            raise ReconstructionWorkspaceError("reconstruction source must be RAW_CAPTURE")
        try:
            return self.layout.path("raw", safe_relative_path(normalized[4:]))
        except ProjectLayoutError as error:
            raise ReconstructionWorkspaceError("RAW_CAPTURE source path is unsafe") from error
