"""Resource admission for a future local VGGT engine.

This module reads checkpoint metadata only. It never imports model libraries or
opens checkpoint contents. Passing admission is a configured floor, not proof
that VGGT inference will fit or succeed.
"""

from __future__ import annotations

import ctypes
import json
import math
import os
import re
import stat
import subprocess
import tempfile
import threading
import time
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .neural_reconstruction import (
    VGGT_COMMERCIAL_CHECKPOINT_SHA256,
    VGGT_COMMERCIAL_CHECKPOINT_SIZE_BYTES,
    VGGTWorkspaceCamera,
    VGGTWorkspaceEngine,
    VGGTWorkspaceInference,
)
from .neural_reconstruction_io import (
    VGGTImagePreprocessTransform,
    VGGTOutputArtifact,
    VGGTResolvedImage,
)
from .reconstruction import CancelToken

VGGT_UPSTREAM_CODE_COMMIT = "a288dd0f14786c93483e45524328726ab7b1b4ce"
_WORKER_RESULT_SCHEMA = "packlab.vggt-worker-result.v1"
_WORKER_LIMITATIONS = (
    "CPU VGGT output is experimental observation only.",
    "Point cloud is deterministically capped at 50000 finite samples.",
    "Scale is relative and has not been metrically verified.",
)
_MAX_WORKER_RESULT_BYTES = 4 * 1024 * 1024
_MAX_WORKER_REQUEST_BYTES = 1 * 1024 * 1024
_MAX_WORKER_IMAGES = 100
_MAX_WORKER_ASSET_ID_CHARS = 1024
_MAX_WORKER_TIMEOUT_SECONDS = 3600
_MAX_POINT_CLOUD_BYTES = 12 * 1024 * 1024
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_HUB_TOKEN_ENV_VARS = (
    "HF_TOKEN",
    "HF_TOKEN_PATH",
    "HUGGING_FACE_HUB_TOKEN",
    "HUGGINGFACE_HUB_TOKEN",
)


def _vggt_worker_environment(
    base_environment: Mapping[str, str], core_source: Path, upstream_root: Path
) -> dict[str, str]:
    environment = dict(base_environment)
    environment["PYTHONPATH"] = os.pathsep.join((str(core_source), str(upstream_root)))
    environment["HF_HUB_OFFLINE"] = "1"
    environment["TRANSFORMERS_OFFLINE"] = "1"
    environment["HF_HUB_DISABLE_TELEMETRY"] = "1"
    environment["CUDA_VISIBLE_DEVICES"] = ""
    for secret_name in _HUB_TOKEN_ENV_VARS:
        environment.pop(secret_name, None)
    return environment


def _vggt_worker_command(python_executable: Path, request_path: Path) -> list[str]:
    """Worker command line that cannot import code planted in its working directory.

    ``-P`` stops ``-m`` from prepending the working directory to ``sys.path`` and ``-s``
    skips the user site-packages, so only PYTHONPATH (pinned core + upstream) and the
    interpreter's own site-packages are importable.
    """
    return [
        str(python_executable),
        "-B",
        "-P",
        "-s",
        "-m",
        "packlab_core.vggt_worker",
        "--request",
        str(request_path),
    ]


class VGGTWorkerError(RuntimeError):
    """The isolated local VGGT worker failed its bounded protocol."""


def _encode_worker_request(request: dict[str, object]) -> bytes:
    try:
        encoded = json.dumps(request, sort_keys=True, separators=(",", ":")).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as error:
        raise VGGTWorkerError("local VGGT worker request is not serializable") from error
    if not 0 < len(encoded) <= _MAX_WORKER_REQUEST_BYTES:
        raise VGGTWorkerError("local VGGT worker request exceeded its size limit")
    return encoded


class VGGTSubprocessWorkspaceEngine:
    """Run pinned local VGGT CPU inference in a private offline worker process.

    Construct this engine only from ``LazyGuardedVGGTWorkspaceEngine`` after
    its memory admission floor passes. The worker and checkpoint are never
    imported/opened by capability probing.
    """

    def __init__(
        self,
        python_executable: str | Path,
        upstream_root: str | Path,
        checkpoint_path: str | Path,
        runtime_output_root: str | Path,
        *,
        expected_checkpoint_size_bytes: int,
        memory_budget: VGGTMemoryBudget,
        memory_reader: PhysicalMemoryReader,
        expected_checkpoint_sha256: str = VGGT_COMMERCIAL_CHECKPOINT_SHA256,
        timeout_seconds: float = 3600,
    ) -> None:
        if (
            isinstance(expected_checkpoint_size_bytes, bool)
            or not isinstance(expected_checkpoint_size_bytes, int)
            or expected_checkpoint_size_bytes <= 0
            or not isinstance(expected_checkpoint_sha256, str)
            or _SHA256.fullmatch(expected_checkpoint_sha256) is None
            or expected_checkpoint_size_bytes != VGGT_COMMERCIAL_CHECKPOINT_SIZE_BYTES
            or expected_checkpoint_sha256 != VGGT_COMMERCIAL_CHECKPOINT_SHA256
            or isinstance(timeout_seconds, bool)
            or not isinstance(timeout_seconds, (int, float))
            or not math.isfinite(timeout_seconds)
            or timeout_seconds <= 0
            or timeout_seconds > _MAX_WORKER_TIMEOUT_SECONDS
        ):
            raise ValueError("VGGT worker identity or timeout is invalid")
        self._python = Path(python_executable)
        self._upstream_root = Path(upstream_root)
        self._checkpoint = Path(checkpoint_path)
        self._output_root = Path(runtime_output_root)
        self._checkpoint_size = expected_checkpoint_size_bytes
        self._checkpoint_sha256 = expected_checkpoint_sha256
        self._memory_budget = memory_budget
        self._memory_reader = memory_reader
        self._timeout = timeout_seconds
        self._core_source = Path(__file__).resolve().parents[1]
        if memory_budget.checkpoint_bytes != expected_checkpoint_size_bytes:
            raise ValueError("VGGT worker memory budget does not match the pinned checkpoint")

    def available(self) -> bool:
        try:
            if (
                not self._python.is_file()
                or _is_reparse_path(self._python)
                or not self._core_source.is_dir()
                or _is_reparse_path(self._core_source)
            ):
                return False
            if not self._upstream_root.is_dir() or not self._output_root.is_dir():
                return False
            if _is_reparse_path(self._upstream_root) or _is_reparse_path(self._output_root):
                return False
            checkpoint_stat = self._checkpoint.lstat()
            if (
                not stat.S_ISREG(checkpoint_stat.st_mode)
                or _is_reparse_path(self._checkpoint)
                or checkpoint_stat.st_size != self._checkpoint_size
            ):
                return False
            revision = subprocess.check_output(
                ["git", "-C", str(self._upstream_root), "rev-parse", "HEAD"],
                text=True,
                stderr=subprocess.DEVNULL,
                timeout=5,
            ).strip()
            if revision != VGGT_UPSTREAM_CODE_COMMIT:
                return False
            dirty = subprocess.check_output(
                ["git", "-C", str(self._upstream_root), "status", "--porcelain"],
                text=True,
                stderr=subprocess.DEVNULL,
                timeout=5,
            )
            if dirty.strip():
                return False
            _admit_checkpoint_and_memory(self._checkpoint, self._memory_budget, self._memory_reader)
            return True
        except (OSError, subprocess.SubprocessError, ValueError):
            return False

    def infer(self, images, cancel) -> VGGTWorkspaceInference:
        if cancel.cancelled:
            return VGGTWorkspaceInference("cancelled", (), (), point_count=0)
        if not isinstance(images, tuple) or not 1 <= len(images) <= _MAX_WORKER_IMAGES:
            raise VGGTWorkerError("local VGGT worker image count is invalid")
        _admit_checkpoint_and_memory(self._checkpoint, self._memory_budget, self._memory_reader)
        if not self.available():
            raise VGGTWorkerError("pinned local VGGT worker prerequisites are unavailable")
        output_root = self._output_root.resolve(strict=True)
        temp_root = tempfile.TemporaryDirectory(prefix=".packlab-vggt-worker-", dir=output_root)
        try:
            work = Path(temp_root.name)
            request_path = work / "request.json"
            result_path = work / "result.json"
            point_path = work / "points.ply"
            request = {
                "schema": "packlab.vggt-worker-request.v1",
                "upstream_root": str(self._upstream_root.resolve(strict=True)),
                "upstream_commit": VGGT_UPSTREAM_CODE_COMMIT,
                "checkpoint_path": str(self._checkpoint.resolve(strict=True)),
                "checkpoint_size_bytes": self._checkpoint_size,
                "checkpoint_sha256": self._checkpoint_sha256,
                "required_available_memory_bytes": self._memory_budget.required_available_bytes,
                "images": [
                    {
                        "asset_id": image.asset_id,
                        "path": str(image.path.resolve(strict=True)),
                        "sha256": image.sha256,
                        "size_bytes": image.size_bytes,
                    }
                    for image in images
                ],
                "result_path": str(result_path),
                "point_cloud_path": str(point_path),
            }
            if any(
                not isinstance(image.asset_id, str)
                or not image.asset_id
                or len(image.asset_id) > _MAX_WORKER_ASSET_ID_CHARS
                for image in images
            ):
                raise VGGTWorkerError("local VGGT worker asset ID is invalid")
            request_path.write_bytes(_encode_worker_request(request))
            environment = _vggt_worker_environment(
                os.environ,
                self._core_source,
                self._upstream_root.resolve(strict=True),
            )
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
            try:
                process = subprocess.Popen(
                    _vggt_worker_command(self._python, request_path),
                    # Private per-job directory, never the shared output root (review P2).
                    cwd=work,
                    env=environment,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=flags,
                )
            except OSError as error:
                raise VGGTWorkerError("local VGGT worker could not start") from error
            if not _wait_for_vggt_worker(process, cancel, self._timeout):
                return VGGTWorkspaceInference("cancelled", (), (), point_count=0)
            result = _read_worker_result(result_path, images)
            _validate_worker_point_cloud(point_path, result.point_count)
            retained_point_path = output_root / f".packlab-vggt-points-{uuid.uuid4().hex}.ply"
            os.replace(point_path, retained_point_path)
            artifact = VGGTOutputArtifact(
                "point_cloud", "points.ply", retained_point_path, cleanup_after_publish=True
            )
            return VGGTWorkspaceInference(
                result.reconstruction_revision,
                result.cameras,
                (artifact,),
                result.point_count,
                triangle_count=0,
                limitations=result.limitations,
            )
        finally:
            temp_root.cleanup()


@dataclass(frozen=True, slots=True)
class _ParsedVGGTWorkerResult:
    reconstruction_revision: str
    cameras: tuple[VGGTWorkspaceCamera, ...]
    point_count: int
    limitations: tuple[str, ...]


def _wait_for_vggt_worker(process, cancel: CancelToken, timeout_seconds: float) -> bool:
    """Wait with cancellation and timeout; return false only on cancellation."""

    deadline = time.monotonic() + timeout_seconds
    while process.poll() is None:
        if cancel.cancelled:
            try:
                process.terminate()
            except OSError:
                pass
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            return False
        if time.monotonic() >= deadline:
            process.kill()
            process.wait()
            raise VGGTWorkerError("local VGGT worker exceeded its time limit")
        time.sleep(0.1)
    if process.returncode != 0:
        raise VGGTWorkerError("local VGGT worker failed")
    return True


def _is_reparse_path(path: Path) -> bool:
    try:
        metadata = path.lstat()
    except OSError:
        return True
    attributes = getattr(metadata, "st_file_attributes", 0)
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return path.is_symlink() or bool(reparse and attributes & reparse)


def _finite_tuple(value: object, size: int) -> tuple[float, ...]:
    if (
        not isinstance(value, list)
        or len(value) != size
        or any(isinstance(item, bool) or not isinstance(item, (int, float)) for item in value)
    ):
        raise VGGTWorkerError("VGGT worker returned an invalid camera matrix")
    try:
        converted = tuple(float(item) for item in value)
    except OverflowError as error:
        raise VGGTWorkerError("VGGT worker returned a non-finite camera matrix") from error
    if any(isinstance(item, bool) for item in value) or not all(
        math.isfinite(item) for item in converted
    ):
        raise VGGTWorkerError("VGGT worker returned a non-finite camera matrix")
    return converted


def _unique_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Reject ambiguous duplicate keys in worker-produced JSON records."""

    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("worker JSON contains a duplicate object key")
        value[key] = item
    return value


def _read_worker_result(
    path: Path, images: tuple[VGGTResolvedImage, ...]
) -> _ParsedVGGTWorkerResult:
    try:
        metadata = path.lstat()
        if _is_reparse_path(path) or not stat.S_ISREG(metadata.st_mode):
            raise VGGTWorkerError("VGGT worker result is not a regular file")
        if not 0 < metadata.st_size <= _MAX_WORKER_RESULT_BYTES:
            raise VGGTWorkerError("VGGT worker result size is invalid")
        with path.open("rb") as handle:
            payload = handle.read(_MAX_WORKER_RESULT_BYTES + 1)
        if len(payload) > _MAX_WORKER_RESULT_BYTES:
            raise VGGTWorkerError("VGGT worker result size is invalid")
        value = json.loads(payload.decode("utf-8"), object_pairs_hook=_unique_json_object)
    except VGGTWorkerError:
        raise
    except (OSError, UnicodeError, ValueError) as error:
        raise VGGTWorkerError("VGGT worker result could not be read") from error
    expected = {
        "schema",
        "status",
        "reconstruction_revision",
        "cameras",
        "point_count",
        "triangle_count",
        "point_cloud_filename",
        "limitations",
    }
    if not isinstance(value, dict) or set(value) != expected:
        raise VGGTWorkerError("VGGT worker result fields are invalid")
    if value["schema"] != _WORKER_RESULT_SCHEMA or value["status"] != "ok":
        raise VGGTWorkerError("VGGT worker did not return an inference result")
    revision = value["reconstruction_revision"]
    if not isinstance(revision, str) or not re.fullmatch(r"vggt-[0-9a-f]{32}", revision):
        raise VGGTWorkerError("VGGT worker revision is invalid")
    if value["point_cloud_filename"] != "points.ply":
        raise VGGTWorkerError("VGGT worker point-cloud name is invalid")
    points = value["point_count"]
    triangles = value["triangle_count"]
    if isinstance(points, bool) or not isinstance(points, int) or not 1 <= points <= 50_000:
        raise VGGTWorkerError("VGGT worker point count is invalid")
    if isinstance(triangles, bool) or not isinstance(triangles, int) or triangles != 0:
        raise VGGTWorkerError("VGGT worker triangle count is unsupported")
    camera_values = value["cameras"]
    image_ids = tuple(image.asset_id for image in images)
    if not isinstance(camera_values, list) or len(camera_values) != len(image_ids):
        raise VGGTWorkerError("VGGT worker camera count differs from its inputs")
    cameras = []
    for entry, expected_id, image in zip(camera_values, image_ids, images, strict=True):
        if not isinstance(entry, dict) or set(entry) != {
            "image_asset_id",
            "world_to_camera_opencv",
            "intrinsics_vggt_pixels",
            "transform",
        }:
            raise VGGTWorkerError("VGGT worker camera record is invalid")
        if entry["image_asset_id"] != expected_id:
            raise VGGTWorkerError("VGGT worker camera order differs from its inputs")
        transform_value = entry["transform"]
        if not isinstance(transform_value, dict) or set(transform_value) != {
            "source_width",
            "source_height",
            "pad_left",
            "pad_top",
            "scale",
        }:
            raise VGGTWorkerError("VGGT worker image transform is invalid")
        try:
            transform = VGGTImagePreprocessTransform(**transform_value)
        except (TypeError, ValueError) as error:
            raise VGGTWorkerError("VGGT worker image transform is invalid") from error
        cameras.append(
            VGGTWorkspaceCamera(
                expected_id,
                _finite_tuple(entry["world_to_camera_opencv"], 12),
                _finite_tuple(entry["intrinsics_vggt_pixels"], 9),
                transform,
            )
        )
    limitations = value["limitations"]
    if not isinstance(limitations, list) or tuple(limitations) != _WORKER_LIMITATIONS:
        raise VGGTWorkerError("VGGT worker limitations are invalid")
    return _ParsedVGGTWorkerResult(revision, tuple(cameras), points, _WORKER_LIMITATIONS)


def _validate_worker_point_cloud(path: Path, expected_points: int) -> None:
    try:
        metadata = path.lstat()
        if _is_reparse_path(path) or not stat.S_ISREG(metadata.st_mode):
            raise VGGTWorkerError("VGGT worker point cloud is not a regular file")
        if metadata.st_size > _MAX_POINT_CLOUD_BYTES:
            raise VGGTWorkerError("VGGT worker point cloud exceeded its size limit")
        with path.open("rb") as handle:
            payload = handle.read(_MAX_POINT_CLOUD_BYTES + 1)
    except VGGTWorkerError:
        raise
    except OSError as error:
        raise VGGTWorkerError("VGGT worker point cloud is unavailable") from error
    if len(payload) > _MAX_POINT_CLOUD_BYTES:
        raise VGGTWorkerError("VGGT worker point cloud exceeded its size limit")
    lines = payload.splitlines()
    expected_header = [
        b"ply",
        b"format ascii 1.0",
        None,
        b"property float x",
        b"property float y",
        b"property float z",
        b"end_header",
    ]
    if (
        lines[:2] != expected_header[:2]
        or len(lines) < len(expected_header)
        or not lines[2].startswith(b"element vertex ")
        or lines[3 : len(expected_header)] != expected_header[3:]
    ):
        raise VGGTWorkerError("VGGT worker point cloud header is invalid")
    try:
        declared_count = int(lines[2][len(b"element vertex ") :])
    except ValueError as error:
        raise VGGTWorkerError("VGGT worker point cloud header is invalid") from error
    if declared_count != expected_points:
        raise VGGTWorkerError("VGGT worker point cloud count differs")
    point_lines = lines[len(expected_header) :]
    if len(point_lines) != expected_points:
        raise VGGTWorkerError("VGGT worker point cloud count differs")
    for line in point_lines:
        try:
            values = line.split()
            if len(values) != 3 or not all(math.isfinite(float(value)) for value in values):
                raise ValueError("invalid point")
        except (ValueError, OverflowError) as error:
            raise VGGTWorkerError("VGGT worker point cloud contains an invalid point") from error


class VGGTMemoryAdmissionError(RuntimeError):
    """Raised before inference when a configured resource gate is not satisfied."""


@dataclass(frozen=True, slots=True)
class VGGTMemorySnapshot:
    total_physical_bytes: int
    available_physical_bytes: int

    def __post_init__(self) -> None:
        values = (self.total_physical_bytes, self.available_physical_bytes)
        if any(
            isinstance(value, bool) or not isinstance(value, int) or value <= 0 for value in values
        ):
            raise ValueError("physical memory values must be positive integers")
        if self.available_physical_bytes > self.total_physical_bytes:
            raise ValueError("available physical memory exceeds total physical memory")


@dataclass(frozen=True, slots=True)
class VGGTMemoryBudget:
    checkpoint_bytes: int
    inference_reserve_bytes: int

    def __post_init__(self) -> None:
        values = (self.checkpoint_bytes, self.inference_reserve_bytes)
        if any(
            isinstance(value, bool) or not isinstance(value, int) or value <= 0 for value in values
        ):
            raise ValueError("VGGT memory budget values must be positive integers")

    @property
    def required_available_bytes(self) -> int:
        return self.checkpoint_bytes + self.inference_reserve_bytes


class PhysicalMemoryReader(Protocol):
    def snapshot(self) -> VGGTMemorySnapshot: ...


class WindowsPhysicalMemoryReader:
    """Read system-wide physical memory counters via the Windows API."""

    def snapshot(self) -> VGGTMemorySnapshot:
        if os.name != "nt":
            raise OSError("physical memory reader requires Windows")

        class MemoryStatusEx(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        status = MemoryStatusEx()
        status.dwLength = ctypes.sizeof(MemoryStatusEx)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        if not kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            error_code = ctypes.get_last_error()
            raise OSError(error_code, "GlobalMemoryStatusEx failed")
        return VGGTMemorySnapshot(int(status.ullTotalPhys), int(status.ullAvailPhys))


class GuardedVGGTWorkspaceEngine:
    """Block injected inference until checkpoint metadata and RAM floor pass."""

    def __init__(
        self,
        engine: VGGTWorkspaceEngine,
        checkpoint_path: str | Path,
        budget: VGGTMemoryBudget,
        memory_reader: PhysicalMemoryReader,
    ) -> None:
        self._engine = engine
        self._checkpoint_path = Path(checkpoint_path)
        self._budget = budget
        self._memory_reader = memory_reader
        if budget.checkpoint_bytes <= 0:
            raise ValueError("checkpoint size must be positive")

    def _admit(self) -> None:
        _admit_checkpoint_and_memory(self._checkpoint_path, self._budget, self._memory_reader)

    def available(self) -> bool:
        try:
            self._admit()
            return self._engine.available()
        except Exception:
            return False

    def infer(
        self,
        images: tuple[VGGTResolvedImage, ...],
        cancel: CancelToken,
    ) -> VGGTWorkspaceInference:
        self._admit()
        return self._engine.infer(images, cancel)


class LazyGuardedVGGTWorkspaceEngine:
    """Create the runtime engine only after checkpoint and RAM admission pass.

    The factory is invoked at first inference, never from construction or
    capability probing. This lets a factory import model libraries and load
    weights only after the configured resource gate succeeds.
    """

    def __init__(
        self,
        engine_factory: Callable[[], VGGTWorkspaceEngine],
        availability_probe: Callable[[], bool],
        checkpoint_path: str | Path,
        budget: VGGTMemoryBudget,
        memory_reader: PhysicalMemoryReader,
    ) -> None:
        if not callable(engine_factory) or not callable(availability_probe):
            raise TypeError("VGGT engine factory and availability probe must be callable")
        self._engine_factory = engine_factory
        self._availability_probe = availability_probe
        self._checkpoint_path = Path(checkpoint_path)
        self._budget = budget
        self._memory_reader = memory_reader
        self._engine: VGGTWorkspaceEngine | None = None
        self._engine_lock = threading.Lock()

    def _admit(self) -> None:
        _admit_checkpoint_and_memory(self._checkpoint_path, self._budget, self._memory_reader)

    def available(self) -> bool:
        try:
            self._admit()
            if self._engine is not None:
                return bool(self._engine.available())
            return bool(self._availability_probe())
        except Exception:
            return False

    def _get_engine(self) -> VGGTWorkspaceEngine:
        if self._engine is not None:
            return self._engine
        with self._engine_lock:
            if self._engine is not None:
                return self._engine
            try:
                engine = self._engine_factory()
            except Exception as error:
                raise VGGTMemoryAdmissionError(
                    "VGGT engine initialization failed after resource admission"
                ) from error
            if not callable(getattr(engine, "available", None)) or not callable(
                getattr(engine, "infer", None)
            ):
                raise VGGTMemoryAdmissionError("VGGT engine factory returned an invalid engine")
            self._engine = engine
            return engine

    def infer(
        self,
        images: tuple[VGGTResolvedImage, ...],
        cancel: CancelToken,
    ) -> VGGTWorkspaceInference:
        if cancel.cancelled:
            return VGGTWorkspaceInference("cancelled", (), (), point_count=0)
        self._admit()
        if self._engine is None:
            try:
                available = self._availability_probe()
            except Exception as error:
                raise VGGTMemoryAdmissionError(
                    "VGGT runtime prerequisites could not be checked"
                ) from error
            if not available:
                raise VGGTMemoryAdmissionError("VGGT runtime prerequisites are unavailable")
        engine = self._get_engine()
        if cancel.cancelled:
            return VGGTWorkspaceInference("cancelled", (), (), point_count=0)
        return engine.infer(images, cancel)


def _admit_checkpoint_and_memory(
    checkpoint_path: Path,
    budget: VGGTMemoryBudget,
    memory_reader: PhysicalMemoryReader,
) -> None:
    try:
        metadata = checkpoint_path.lstat()
    except OSError as error:
        raise VGGTMemoryAdmissionError("pinned VGGT checkpoint is unavailable") from error
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_size != budget.checkpoint_bytes:
        raise VGGTMemoryAdmissionError("pinned VGGT checkpoint size does not match configuration")
    try:
        memory = memory_reader.snapshot()
    except Exception as error:
        raise VGGTMemoryAdmissionError("available physical memory could not be measured") from error
    required = budget.required_available_bytes
    if memory.available_physical_bytes < required:
        raise VGGTMemoryAdmissionError(
            "insufficient available physical memory for configured VGGT budget"
        )
