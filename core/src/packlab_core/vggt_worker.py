"""Offline CPU VGGT worker entrypoint.

This module is launched only by ``VGGTSubprocessWorkspaceEngine`` after its
caller has passed the physical-memory admission gate. Importing it does not
import torch or construct the VGGT model.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import stat
import subprocess
import uuid
from pathlib import Path
from typing import Any

_REQUEST_SCHEMA = "packlab.vggt-worker-request.v1"
_RESULT_SCHEMA = "packlab.vggt-worker-result.v1"
_MAX_REQUEST_BYTES = 1024 * 1024
_MAX_RESULT_BYTES = 4 * 1024 * 1024
_MAX_IMAGES = 100
_MAX_ASSET_ID_CHARS = 1024
_MAX_POINTS = 50_000
_CHUNK_BYTES = 1024 * 1024
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_PINNED_UPSTREAM_COMMIT = "a288dd0f14786c93483e45524328726ab7b1b4ce"
_PINNED_CHECKPOINT_SIZE = 5_026_367_224
_PINNED_CHECKPOINT_SHA256 = "2b766b284359bc47ce26be107254621f685b758a0282082ff109f3ff02788b53"
_HUB_TOKEN_ENV_VARS = (
    "HF_TOKEN",
    "HF_TOKEN_PATH",
    "HUGGING_FACE_HUB_TOKEN",
    "HUGGINGFACE_HUB_TOKEN",
)


class WorkerRequestError(ValueError):
    """A worker request failed closed validation."""


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Reject ambiguous duplicate keys in a worker request."""

    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("worker JSON contains a duplicate object key")
        value[key] = item
    return value


def _configure_offline_cpu_environment() -> None:
    """Disable Hub access and make CPU-only execution the worker default."""

    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    for secret_name in _HUB_TOKEN_ENV_VARS:
        os.environ.pop(secret_name, None)


def _write_error_result_exclusive(path: Path) -> None:
    """Record a generic failure only when the worker result path is unused."""

    payload = json.dumps(
        {"schema": _RESULT_SCHEMA, "status": "error", "error": "worker_failed"},
        separators=(",", ":"),
    ).encode("ascii")
    with path.open("xb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())


def _require_worker_memory(required_bytes: int, available_bytes: int) -> None:
    if (
        isinstance(required_bytes, bool)
        or not isinstance(required_bytes, int)
        or required_bytes <= 0
        or isinstance(available_bytes, bool)
        or not isinstance(available_bytes, int)
        or available_bytes < required_bytes
    ):
        raise WorkerRequestError("worker physical-memory admission failed")


def _is_reparse(path: Path) -> bool:
    try:
        metadata = path.lstat()
    except OSError:
        return True
    attributes = getattr(metadata, "st_file_attributes", 0)
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return path.is_symlink() or bool(reparse and attributes & reparse)


def _regular_file(path: Path) -> os.stat_result:
    if _is_reparse(path):
        raise WorkerRequestError("worker input is not a regular file")
    metadata = path.stat()
    if not stat.S_ISREG(metadata.st_mode):
        raise WorkerRequestError("worker input is not a regular file")
    return metadata


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(_CHUNK_BYTES), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_worker_request(request_path: str | Path) -> dict[str, Any]:
    """Read a bounded request document and validate all local file identities."""

    request_file = Path(request_path)
    metadata = _regular_file(request_file)
    if metadata.st_size <= 0 or metadata.st_size > _MAX_REQUEST_BYTES:
        raise WorkerRequestError("worker request size is invalid")
    try:
        with request_file.open("rb") as handle:
            payload = handle.read(_MAX_REQUEST_BYTES + 1)
        if len(payload) > _MAX_REQUEST_BYTES:
            raise WorkerRequestError("worker request size is invalid")
        request = json.loads(payload.decode("utf-8"), object_pairs_hook=_unique_json_object)
    except WorkerRequestError:
        raise
    except (OSError, UnicodeError, ValueError) as error:
        raise WorkerRequestError("worker request is invalid") from error
    required = {
        "schema",
        "upstream_root",
        "upstream_commit",
        "checkpoint_path",
        "checkpoint_size_bytes",
        "checkpoint_sha256",
        "required_available_memory_bytes",
        "images",
        "result_path",
        "point_cloud_path",
    }
    if not isinstance(request, dict) or set(request) != required:
        raise WorkerRequestError("worker request fields are invalid")
    if request["schema"] != _REQUEST_SCHEMA:
        raise WorkerRequestError("worker request schema is unsupported")
    if not isinstance(request["upstream_commit"], str) or not re.fullmatch(
        r"[0-9a-f]{40}", request["upstream_commit"]
    ):
        raise WorkerRequestError("upstream revision is invalid")
    if request["upstream_commit"] != _PINNED_UPSTREAM_COMMIT:
        raise WorkerRequestError("upstream revision is not the PackLab pin")
    if not isinstance(request["checkpoint_sha256"], str) or not _SHA256.fullmatch(
        request["checkpoint_sha256"]
    ):
        raise WorkerRequestError("checkpoint digest is invalid")
    size = request["checkpoint_size_bytes"]
    if isinstance(size, bool) or not isinstance(size, int) or size <= 0:
        raise WorkerRequestError("checkpoint size is invalid")
    if size != _PINNED_CHECKPOINT_SIZE or request["checkpoint_sha256"] != _PINNED_CHECKPOINT_SHA256:
        raise WorkerRequestError("checkpoint identity is not the PackLab pin")
    required_memory = request["required_available_memory_bytes"]
    if (
        isinstance(required_memory, bool)
        or not isinstance(required_memory, int)
        or required_memory <= size
    ):
        raise WorkerRequestError("worker physical-memory budget is invalid")

    source_root = Path(request["upstream_root"])
    if not source_root.is_absolute() or _is_reparse(source_root) or not source_root.is_dir():
        raise WorkerRequestError("pinned upstream source is unavailable")
    try:
        observed_commit = subprocess.check_output(
            ["git", "-C", str(source_root), "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=10,
        ).strip()
    except (OSError, subprocess.SubprocessError) as error:
        raise WorkerRequestError("pinned upstream source could not be verified") from error
    if observed_commit != request["upstream_commit"]:
        raise WorkerRequestError("pinned upstream source revision differs")
    try:
        dirty = subprocess.check_output(
            ["git", "-C", str(source_root), "status", "--porcelain"],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise WorkerRequestError("pinned upstream source status could not be verified") from error
    if dirty.strip():
        raise WorkerRequestError("pinned upstream source has local modifications")

    checkpoint = Path(request["checkpoint_path"])
    if not checkpoint.is_absolute():
        raise WorkerRequestError("pinned checkpoint path is not absolute")
    checkpoint_metadata = _regular_file(checkpoint)
    if checkpoint_metadata.st_size != size:
        raise WorkerRequestError("pinned checkpoint size differs")
    if _sha256_path(checkpoint) != request["checkpoint_sha256"]:
        raise WorkerRequestError("pinned checkpoint digest differs")

    images = request["images"]
    if not isinstance(images, list) or not 1 <= len(images) <= _MAX_IMAGES:
        raise WorkerRequestError("worker image count is invalid")
    seen_asset_ids: set[str] = set()
    for image in images:
        if not isinstance(image, dict) or set(image) != {
            "asset_id",
            "path",
            "sha256",
            "size_bytes",
        }:
            raise WorkerRequestError("worker image entry is invalid")
        if (
            not isinstance(image["asset_id"], str)
            or not image["asset_id"]
            or len(image["asset_id"]) > _MAX_ASSET_ID_CHARS
            or image["asset_id"].startswith("/")
            or "\\" in image["asset_id"]
            or any(part in {"", ".", ".."} for part in image["asset_id"].split("/"))
            or re.match(r"^[A-Za-z]:", image["asset_id"]) is not None
            or not isinstance(image["sha256"], str)
            or not _SHA256.fullmatch(image["sha256"])
        ):
            raise WorkerRequestError("worker image identity is invalid")
        if image["asset_id"] in seen_asset_ids:
            raise WorkerRequestError("worker image IDs are duplicated")
        seen_asset_ids.add(image["asset_id"])
        image_size = image["size_bytes"]
        if isinstance(image_size, bool) or not isinstance(image_size, int) or image_size <= 0:
            raise WorkerRequestError("worker image size is invalid")
        image_path = Path(image["path"])
        if not image_path.is_absolute():
            raise WorkerRequestError("worker image path is not absolute")
        image_metadata = _regular_file(image_path)
        if image_metadata.st_size != image_size or _sha256_path(image_path) != image["sha256"]:
            raise WorkerRequestError("worker image digest differs")

    request_parent = request_file.parent.resolve(strict=True)
    for name, expected_name in (("result_path", "result.json"), ("point_cloud_path", "points.ply")):
        output_path = Path(request[name])
        if (
            not output_path.is_absolute()
            or output_path.name != expected_name
            or output_path.parent.resolve(strict=True) != request_parent
        ):
            raise WorkerRequestError("worker output path is outside its private request directory")
        if output_path.exists() or _is_reparse(output_path):
            raise WorkerRequestError("worker output path already exists")
    return request


def _write_point_cloud(points: Any, destination: Path) -> int:
    """Write a deterministic, finite, capped XYZ point sample as ASCII PLY."""

    import numpy as np

    point_rows = points.reshape(-1, 3)
    rows_per_chunk = 65_536
    finite_total = 0
    for start in range(0, int(point_rows.shape[0]), rows_per_chunk):
        block = point_rows[start : start + rows_per_chunk]
        finite_total += int(np.isfinite(block).all(axis=1).sum())
    if finite_total == 0:
        raise WorkerRequestError("VGGT worker produced no finite point samples")
    stride = max(1, math.ceil(finite_total / _MAX_POINTS))
    expected_count = math.ceil(finite_total / stride)
    count = 0
    finite_index = 0
    with destination.open("x", encoding="ascii", newline="\n") as handle:
        handle.write(
            "ply\nformat ascii 1.0\n"
            f"element vertex {expected_count}\n"
            "property float x\nproperty float y\nproperty float z\nend_header\n"
        )
        for start in range(0, int(point_rows.shape[0]), rows_per_chunk):
            block = point_rows[start : start + rows_per_chunk]
            finite_rows = np.isfinite(block).all(axis=1)
            for row, is_finite in zip(block, finite_rows, strict=True):
                if not is_finite:
                    continue
                if finite_index % stride == 0:
                    x, y, z = (float(value) for value in row)
                    handle.write(f"{x:.9g} {-y:.9g} {-z:.9g}\n")
                    count += 1
                finite_index += 1
        if count != expected_count:
            raise WorkerRequestError("VGGT point sample count changed while writing")
        handle.flush()
        os.fsync(handle.fileno())
    return count


def run_local_inference(request: dict[str, Any]) -> dict[str, Any]:
    """Load the pinned local model and run CPU inference; called only by CLI."""

    # These are set by the parent before interpreter startup as well. Reassert
    # them before importing torch or the upstream model package.
    _configure_offline_cpu_environment()

    from packlab_core.neural_reconstruction_runtime import WindowsPhysicalMemoryReader

    available_memory = WindowsPhysicalMemoryReader().snapshot().available_physical_bytes
    _require_worker_memory(request["required_available_memory_bytes"], available_memory)

    import torch
    import torch.nn.functional as functional
    from vggt.models.vggt import VGGT
    from vggt.utils.load_fn import load_and_preprocess_images_square
    from vggt.utils.pose_enc import pose_encoding_to_extri_intri

    from packlab_core.neural_reconstruction import VGGT_COMMERCIAL_CHECKPOINT_SHA256
    from packlab_core.vggt_checkpoint import load_safetensors_into_cpu_model

    cpu = torch.device("cpu")
    model = VGGT().to(device=cpu)
    loaded = load_safetensors_into_cpu_model(
        model,
        request["checkpoint_path"],
        expected_size_bytes=request["checkpoint_size_bytes"],
        expected_sha256=request["checkpoint_sha256"],
    )
    if loaded.sha256 != VGGT_COMMERCIAL_CHECKPOINT_SHA256:
        raise WorkerRequestError("loaded checkpoint differs from the PackLab pin")
    model.eval()
    image_paths = [entry["path"] for entry in request["images"]]
    prepared, _ = load_and_preprocess_images_square(image_paths, target_size=1024)
    for entry in request["images"]:
        current = _regular_file(Path(entry["path"]))
        if (
            current.st_size != entry["size_bytes"]
            or _sha256_path(Path(entry["path"])) != entry["sha256"]
        ):
            raise WorkerRequestError("worker image changed during preprocessing")
    images = functional.interpolate(
        prepared.to(device=cpu), size=(518, 518), mode="bilinear", align_corners=False
    ).to(device=cpu)
    with torch.inference_mode():
        predictions = model(images.unsqueeze(0))
        extrinsic, intrinsic = pose_encoding_to_extri_intri(
            predictions["pose_enc"], images.shape[-2:]
        )
    extrinsics = extrinsic[0].detach().to(dtype=torch.float32, device="cpu").numpy()
    intrinsics = intrinsic[0].detach().to(dtype=torch.float32, device="cpu").numpy()
    point_map = (
        predictions["world_points"][0].detach().to(dtype=torch.float32, device="cpu").numpy()
    )
    cameras = []
    for index, entry in enumerate(request["images"]):
        width, height = _image_dimensions(entry["path"])
        maximum = max(width, height)
        cameras.append(
            {
                "image_asset_id": entry["asset_id"],
                "world_to_camera_opencv": extrinsics[index].reshape(-1).tolist(),
                "intrinsics_vggt_pixels": intrinsics[index].reshape(-1).tolist(),
                "transform": {
                    "source_width": width,
                    "source_height": height,
                    "pad_left": (maximum - width) / 2,
                    "pad_top": (maximum - height) / 2,
                    "scale": 518 / maximum,
                },
            }
        )
    point_count = _write_point_cloud(point_map, Path(request["point_cloud_path"]))
    return {
        "schema": _RESULT_SCHEMA,
        "status": "ok",
        "reconstruction_revision": f"vggt-{uuid.uuid4().hex}",
        "cameras": cameras,
        "point_count": point_count,
        "triangle_count": 0,
        "point_cloud_filename": Path(request["point_cloud_path"]).name,
        "limitations": [
            "CPU VGGT output is experimental observation only.",
            "Point cloud is deterministically capped at 50000 finite samples.",
            "Scale is relative and has not been metrically verified.",
        ],
    }


def _image_dimensions(path: str) -> tuple[int, int]:
    from PIL import Image

    with Image.open(path) as image:
        width, height = image.size
    if width <= 0 or height <= 0:
        raise WorkerRequestError("worker image dimensions are invalid")
    return width, height


def _main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--request", required=True)
    args = parser.parse_args()
    request: dict[str, Any] | None = None
    try:
        request = read_worker_request(args.request)
        result = run_local_inference(request)
        result_path = Path(request["result_path"])
        try:
            result_payload = (
                json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False).encode(
                    "utf-8"
                )
                + b"\n"
            )
        except (TypeError, ValueError, UnicodeError) as error:
            raise WorkerRequestError("worker result is not serializable") from error
        if len(result_payload) > _MAX_RESULT_BYTES:
            raise WorkerRequestError("worker result exceeded its size limit")
        with result_path.open("xb") as handle:
            handle.write(result_payload)
            handle.flush()
            os.fsync(handle.fileno())
        return 0
    except Exception:
        # Deliberately avoid printing exception strings, which may contain local
        # paths, image names, checkpoint locations or library diagnostics.
        if request is not None:
            try:
                _write_error_result_exclusive(Path(request["result_path"]))
            except (OSError, KeyError, TypeError):
                pass
        return 1


if __name__ == "__main__":
    raise SystemExit(_main())
