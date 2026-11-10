from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import pytest

from packlab_core.neural_reconstruction_io import VGGTResolvedImage
from packlab_core.neural_reconstruction_runtime import (
    VGGTMemoryBudget,
    VGGTSubprocessWorkspaceEngine,
    VGGTWorkerError,
    _encode_worker_request,
    _read_worker_result,
    _validate_worker_point_cloud,
    _vggt_worker_environment,
    _wait_for_vggt_worker,
)
from packlab_core.reconstruction import CancelToken
from packlab_core.vggt_worker import (
    WorkerRequestError,
    _configure_offline_cpu_environment,
    _require_worker_memory,
    _write_error_result_exclusive,
    _write_point_cloud,
    read_worker_request,
)


def _result(image_id: str = "working/one.jpg") -> dict[str, object]:
    return {
        "schema": "packlab.vggt-worker-result.v1",
        "status": "ok",
        "reconstruction_revision": "vggt-0123456789abcdef0123456789abcdef",
        "cameras": [
            {
                "image_asset_id": image_id,
                "world_to_camera_opencv": [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0],
                "intrinsics_vggt_pixels": [500, 0, 259, 0, 500, 259, 0, 0, 1],
                "transform": {
                    "source_width": 100,
                    "source_height": 50,
                    "pad_left": 25,
                    "pad_top": 0,
                    "scale": 5.18,
                },
            }
        ],
        "point_count": 3,
        "triangle_count": 0,
        "point_cloud_filename": "points.ply",
        "limitations": [
            "CPU VGGT output is experimental observation only.",
            "Point cloud is deterministically capped at 50000 finite samples.",
            "Scale is relative and has not been metrically verified.",
        ],
    }


def test_worker_result_protocol_accepts_ordered_finite_synthetic_record(tmp_path: Path) -> None:
    path = tmp_path / "result.json"
    path.write_text(json.dumps(_result()), encoding="utf-8")
    image = VGGTResolvedImage("working/one.jpg", tmp_path / "one.jpg", "a" * 64, 1)

    result = _read_worker_result(path, (image,))

    assert result.reconstruction_revision == "vggt-0123456789abcdef0123456789abcdef"
    assert result.cameras[0].transform.pad_left == 25
    assert result.point_count == 3


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda value: value.update(schema="unknown"), "did not return"),
        (lambda value: value.update(reconstruction_revision="../escape"), "revision"),
        (
            lambda value: value["cameras"][0].update(image_asset_id="working/other.jpg"),
            "order differs",
        ),
        (
            lambda value: value["cameras"][0].update(
                world_to_camera_opencv=[float("nan")] + [0] * 11
            ),
            "non-finite",
        ),
        (
            lambda value: value["cameras"][0].update(world_to_camera_opencv=[10**1000] + [0] * 11),
            "non-finite",
        ),
        (lambda value: value.update(point_count=0), "point count"),
        (lambda value: value.update(point_count=50_001), "point count"),
        (lambda value: value.update(point_cloud_filename="../../owner.ply"), "name is invalid"),
    ],
)
def test_worker_result_protocol_rejects_invalid_records(
    tmp_path: Path, mutate, message: str
) -> None:
    value = _result()
    mutate(value)
    path = tmp_path / "result.json"
    path.write_text(json.dumps(value), encoding="utf-8")
    image = VGGTResolvedImage("working/one.jpg", tmp_path / "one.jpg", "a" * 64, 1)

    with pytest.raises(VGGTWorkerError, match=message):
        _read_worker_result(path, (image,))


def test_worker_result_protocol_rejects_duplicate_json_keys(tmp_path: Path) -> None:
    path = tmp_path / "result.json"
    payload = json.dumps(_result()).replace('"schema":', '"schema": "duplicate", "schema":', 1)
    path.write_text(payload, encoding="utf-8")
    image = VGGTResolvedImage("working/one.jpg", tmp_path / "one.jpg", "a" * 64, 1)

    with pytest.raises(VGGTWorkerError, match="could not be read"):
        _read_worker_result(path, (image,))


def test_worker_result_reader_rejects_oversized_file(tmp_path: Path) -> None:
    path = tmp_path / "result.json"
    path.write_bytes(b"x" * (4 * 1024 * 1024 + 1))
    image = VGGTResolvedImage("working/one.jpg", tmp_path / "one.jpg", "a" * 64, 1)

    with pytest.raises(VGGTWorkerError, match="result size is invalid"):
        _read_worker_result(path, (image,))


def test_worker_point_cloud_requires_bounded_ascii_ply_and_matching_count(tmp_path: Path) -> None:
    path = tmp_path / "points.ply"
    path.write_bytes(
        b"ply\nformat ascii 1.0\nelement vertex 2\n"
        b"property float x\nproperty float y\nproperty float z\nend_header\n0 0 0\n1 2 3\n"
    )

    _validate_worker_point_cloud(path, 2)
    with pytest.raises(VGGTWorkerError, match="count differs"):
        _validate_worker_point_cloud(path, 3)


def test_worker_point_cloud_rejects_non_ply_file(tmp_path: Path) -> None:
    path = tmp_path / "points.ply"
    path.write_text("not a ply", encoding="ascii")

    with pytest.raises(VGGTWorkerError, match="header is invalid"):
        _validate_worker_point_cloud(path, 0)


@pytest.mark.parametrize(
    "vertices",
    [b"0 0 nan\n", b"0 0 inf\n", b"0 0\n", b"0 0 0\nextra\n"],
)
def test_worker_point_cloud_rejects_nonfinite_or_wrong_vertex_rows(
    tmp_path: Path, vertices: bytes
) -> None:
    path = tmp_path / "points.ply"
    path.write_bytes(
        b"ply\nformat ascii 1.0\nelement vertex 1\n"
        b"property float x\nproperty float y\nproperty float z\nend_header\n" + vertices
    )

    with pytest.raises(VGGTWorkerError, match="invalid point|count differs"):
        _validate_worker_point_cloud(path, 1)


def test_worker_point_cloud_writer_caps_to_finite_packscan_axis_sample(tmp_path: Path) -> None:
    path = tmp_path / "points.ply"
    points = np.asarray(
        [[float(index), float(index + 1), float(index + 2)] for index in range(12)]
        + [[4.0, float("nan"), 6.0]]
    )

    count = _write_point_cloud(points, path)

    assert count == 12
    rows = path.read_text(encoding="ascii").splitlines()
    assert rows[:7] == [
        "ply",
        "format ascii 1.0",
        "element vertex 12",
        "property float x",
        "property float y",
        "property float z",
        "end_header",
    ]
    assert rows[7:] == [f"{index} {-index - 1} {-index - 2}" for index in range(12)]


def test_worker_point_cloud_writer_rejects_empty_finite_sample(tmp_path: Path) -> None:
    path = tmp_path / "points.ply"
    points = np.asarray([[[float("nan"), 2.0, 3.0], [float("inf"), 5.0, 6.0]]])

    with pytest.raises(WorkerRequestError, match="no finite point samples"):
        _write_point_cloud(points, path)

    assert not path.exists()


def test_worker_rejects_unpinned_checkpoint_identity_before_accessing_weights(
    tmp_path: Path,
) -> None:
    request = {
        "schema": "packlab.vggt-worker-request.v1",
        "upstream_root": str(tmp_path / "missing-upstream"),
        "upstream_commit": "a288dd0f14786c93483e45524328726ab7b1b4ce",
        "checkpoint_path": str(tmp_path / "missing.safetensors"),
        "checkpoint_size_bytes": 10,
        "checkpoint_sha256": "a" * 64,
        "required_available_memory_bytes": 11,
        "images": [],
        "result_path": str(tmp_path / "result.json"),
        "point_cloud_path": str(tmp_path / "points.ply"),
    }
    path = tmp_path / "request.json"
    path.write_text(json.dumps(request), encoding="utf-8")

    with pytest.raises(WorkerRequestError, match="identity is not the PackLab pin"):
        read_worker_request(path)


def test_worker_request_reader_rejects_duplicate_json_keys(tmp_path: Path) -> None:
    path = tmp_path / "request.json"
    path.write_text('{"schema":"one","schema":"two"}', encoding="utf-8")

    with pytest.raises(WorkerRequestError, match="request is invalid"):
        read_worker_request(path)


def test_worker_memory_admission_requires_full_configured_reserve() -> None:
    _require_worker_memory(100, 100)
    with pytest.raises(WorkerRequestError, match="memory admission failed"):
        _require_worker_memory(100, 99)
    with pytest.raises(WorkerRequestError, match="memory admission failed"):
        _require_worker_memory(True, 100)


def test_worker_request_reader_rejects_oversized_file_before_json_parse(
    tmp_path: Path,
) -> None:
    path = tmp_path / "request.json"
    path.write_bytes(b"x" * (1024 * 1024 + 1))

    with pytest.raises(WorkerRequestError, match="request size is invalid"):
        read_worker_request(path)


def test_worker_error_record_does_not_overwrite_existing_path(tmp_path: Path) -> None:
    path = tmp_path / "result.json"
    path.write_bytes(b"owner file")

    with pytest.raises(FileExistsError):
        _write_error_result_exclusive(path)

    assert path.read_bytes() == b"owner file"


def test_subprocess_engine_rejects_non_pinned_checkpoint_configuration() -> None:
    with pytest.raises(ValueError, match="identity or timeout"):
        VGGTSubprocessWorkspaceEngine(
            "python.exe",
            "upstream",
            "checkpoint.safetensors",
            "output",
            expected_checkpoint_size_bytes=10,
            memory_budget=VGGTMemoryBudget(10, 10),
            memory_reader=object(),
        )


def test_subprocess_engine_enforces_a_maximum_worker_lifetime() -> None:
    with pytest.raises(ValueError, match="identity or timeout"):
        VGGTSubprocessWorkspaceEngine(
            "python.exe",
            "upstream",
            "checkpoint.safetensors",
            "output",
            expected_checkpoint_size_bytes=5_026_367_224,
            memory_budget=VGGTMemoryBudget(5_026_367_224, 1),
            memory_reader=object(),
            timeout_seconds=3601,
        )


def test_worker_request_encoding_is_size_bounded() -> None:
    assert _encode_worker_request({"small": "request"}) == b'{"small":"request"}'
    with pytest.raises(VGGTWorkerError, match="request exceeded its size limit"):
        _encode_worker_request({"large": "x" * (1024 * 1024)})


@pytest.mark.parametrize("image_count", [0, 101])
def test_subprocess_engine_rejects_unbounded_image_count_before_resource_probe(
    image_count: int,
) -> None:
    class MemoryReaderMustNotRun:
        def snapshot(self):
            raise AssertionError("image count must fail before reading resources")

    engine = VGGTSubprocessWorkspaceEngine(
        "python.exe",
        "upstream",
        "checkpoint.safetensors",
        "output",
        expected_checkpoint_size_bytes=5_026_367_224,
        memory_budget=VGGTMemoryBudget(5_026_367_224, 1),
        memory_reader=MemoryReaderMustNotRun(),
    )
    images = tuple(
        VGGTResolvedImage(f"image/{index}.jpg", Path(f"image-{index}.jpg"), "a" * 64, 1)
        for index in range(image_count)
    )

    with pytest.raises(VGGTWorkerError, match="image count is invalid"):
        engine.infer(images, CancelToken())


def test_vggt_child_environment_is_offline_cpu_and_token_free() -> None:
    environment = _vggt_worker_environment(
        {
            "PATH": "synthetic-path",
            "HF_TOKEN": "redacted-test-token",
            "HF_TOKEN_PATH": "synthetic-token-file",
            "HUGGING_FACE_HUB_TOKEN": "redacted-test-token",
            "HUGGINGFACE_HUB_TOKEN": "redacted-test-token",
        },
        Path("/packlab/core/src"),
        Path("/packlab/vggt"),
    )

    assert environment["PATH"] == "synthetic-path"
    assert environment["PYTHONPATH"] == os.pathsep.join(
        (str(Path("/packlab/core/src")), str(Path("/packlab/vggt")))
    )
    assert environment["HF_HUB_OFFLINE"] == "1"
    assert environment["TRANSFORMERS_OFFLINE"] == "1"
    assert environment["HF_HUB_DISABLE_TELEMETRY"] == "1"
    assert environment["CUDA_VISIBLE_DEVICES"] == ""
    assert not any("TOKEN" in name for name in environment)


def test_worker_reasserts_offline_cpu_environment_and_removes_tokens(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HF_HUB_OFFLINE", "0")
    monkeypatch.setenv("TRANSFORMERS_OFFLINE", "0")
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "0")
    monkeypatch.setenv("HF_TOKEN", "redacted-test-token")
    monkeypatch.setenv("HF_TOKEN_PATH", "synthetic-token-file")

    _configure_offline_cpu_environment()

    assert os.environ["HF_HUB_OFFLINE"] == "1"
    assert os.environ["TRANSFORMERS_OFFLINE"] == "1"
    assert os.environ["HF_HUB_DISABLE_TELEMETRY"] == "1"
    assert os.environ["CUDA_VISIBLE_DEVICES"] == ""
    assert "HF_TOKEN" not in os.environ
    assert "HF_TOKEN_PATH" not in os.environ


class _SyntheticProcess:
    def __init__(self, *, completed: int | None = None, timeout_on_wait: bool = False) -> None:
        self.returncode = completed
        self.timeout_on_wait = timeout_on_wait
        self.terminated = False
        self.killed = False
        self.waited = False

    def poll(self) -> int | None:
        return self.returncode

    def terminate(self) -> None:
        self.terminated = True
        self.returncode = -15

    def kill(self) -> None:
        self.killed = True
        self.returncode = -9

    def wait(self, timeout: float | None = None) -> int:
        self.waited = True
        if self.timeout_on_wait and timeout is not None:
            import subprocess

            raise subprocess.TimeoutExpired("synthetic-worker", timeout)
        return self.returncode or 0


def test_worker_wait_returns_cleanly_after_zero_exit() -> None:
    process = _SyntheticProcess(completed=0)

    assert _wait_for_vggt_worker(process, CancelToken(), 10)
    assert not process.terminated and not process.killed


def test_worker_wait_terminates_on_cancellation() -> None:
    process = _SyntheticProcess()
    cancel = CancelToken()
    cancel.cancel()

    assert not _wait_for_vggt_worker(process, cancel, 10)
    assert process.terminated and process.waited and not process.killed


def test_worker_wait_kills_process_when_cancel_termination_times_out() -> None:
    process = _SyntheticProcess(timeout_on_wait=True)
    cancel = CancelToken()
    cancel.cancel()

    assert not _wait_for_vggt_worker(process, cancel, 10)
    assert process.terminated and process.killed and process.waited


def test_worker_wait_kills_process_after_deadline(monkeypatch: pytest.MonkeyPatch) -> None:
    process = _SyntheticProcess()
    times = iter((0.0, 2.0))
    monkeypatch.setattr(
        "packlab_core.neural_reconstruction_runtime.time.monotonic", lambda: next(times)
    )

    with pytest.raises(VGGTWorkerError, match="time limit"):
        _wait_for_vggt_worker(process, CancelToken(), 1)
    assert process.killed and process.waited


def test_worker_wait_rejects_nonzero_exit() -> None:
    process = _SyntheticProcess(completed=7)

    with pytest.raises(VGGTWorkerError, match="worker failed"):
        _wait_for_vggt_worker(process, CancelToken(), 10)


# --- Review mutants N3, N4, N8, N9 (PL-0436): isolate each worker/engine pin. ---


def _pinned_request(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, **overrides):
    """A request that passes every earlier check, using a tiny synthetic checkpoint.

    The real pins (5 GB checkpoint, upstream git checkout) are patched to synthetic values
    so the later checks can be exercised in isolation.
    """
    import hashlib
    import subprocess as subprocess_module

    from packlab_core import vggt_worker

    checkpoint = tmp_path / "synthetic.safetensors"
    checkpoint.write_bytes(b"synthetic-checkpoint-not-a-model")
    digest = hashlib.sha256(checkpoint.read_bytes()).hexdigest()
    monkeypatch.setattr(vggt_worker, "_PINNED_CHECKPOINT_SIZE", checkpoint.stat().st_size)
    monkeypatch.setattr(vggt_worker, "_PINNED_CHECKPOINT_SHA256", digest)
    upstream = tmp_path / "upstream"
    upstream.mkdir()

    def fake_git(command, **_kwargs):
        return vggt_worker._PINNED_UPSTREAM_COMMIT + "\n" if "rev-parse" in command else ""

    monkeypatch.setattr(subprocess_module, "check_output", fake_git)
    image = tmp_path / "img.png"
    image.write_bytes(b"synthetic-image")
    work = tmp_path / "work"
    work.mkdir()
    request = {
        "schema": "packlab.vggt-worker-request.v1",
        "upstream_root": str(upstream),
        "upstream_commit": vggt_worker._PINNED_UPSTREAM_COMMIT,
        "checkpoint_path": str(checkpoint),
        "checkpoint_size_bytes": checkpoint.stat().st_size,
        "checkpoint_sha256": digest,
        "required_available_memory_bytes": checkpoint.stat().st_size + 1,
        "images": [
            {
                "asset_id": "images/000.png",
                "path": str(image),
                "sha256": hashlib.sha256(b"synthetic-image").hexdigest(),
                "size_bytes": len(b"synthetic-image"),
            }
        ],
        "result_path": str(work / "result.json"),
        "point_cloud_path": str(work / "points.ply"),
    }
    request.update(overrides)
    path = work / "request.json"
    path.write_text(json.dumps(request), encoding="utf-8")
    return path, request


def test_pinned_synthetic_request_is_accepted(tmp_path: Path, monkeypatch) -> None:
    path, _request = _pinned_request(tmp_path, monkeypatch)
    assert read_worker_request(path)["schema"] == "packlab.vggt-worker-request.v1"


def test_worker_rejects_a_different_upstream_commit(tmp_path: Path, monkeypatch) -> None:
    # N3: a well-formed but different commit must not reach the git check.
    path, _request = _pinned_request(tmp_path, monkeypatch, upstream_commit="b" * 40)
    with pytest.raises(WorkerRequestError, match="not the PackLab pin"):
        read_worker_request(path)


def test_worker_rejects_output_paths_outside_its_private_directory(
    tmp_path: Path, monkeypatch
) -> None:
    # N4: outputs must live next to the request file, nowhere else.
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    path, _request = _pinned_request(
        tmp_path, monkeypatch, result_path=str(elsewhere / "result.json")
    )
    with pytest.raises(WorkerRequestError, match="outside its private request directory"):
        read_worker_request(path)


def test_worker_rejects_an_image_whose_bytes_differ_from_its_digest(
    tmp_path: Path, monkeypatch
) -> None:
    # N8: same size, different content.
    path, request = _pinned_request(tmp_path, monkeypatch)
    Path(request["images"][0]["path"]).write_bytes(b"tampered-image!")
    with pytest.raises(WorkerRequestError, match="worker image digest differs"):
        read_worker_request(path)


def test_subprocess_engine_rejects_a_wrong_sha_with_the_pinned_size() -> None:
    # N9: only the SHA differs from the pin.
    with pytest.raises(ValueError, match="identity or timeout"):
        VGGTSubprocessWorkspaceEngine(
            "python.exe",
            "upstream",
            "checkpoint.safetensors",
            "output",
            expected_checkpoint_size_bytes=5_026_367_224,
            expected_checkpoint_sha256="0" * 64,
            memory_budget=VGGTMemoryBudget(5_026_367_224, 1),
            memory_reader=object(),
        )


def test_worker_still_refuses_existing_or_linked_output_paths(tmp_path: Path, monkeypatch) -> None:
    path, request = _pinned_request(tmp_path, monkeypatch)
    Path(request["point_cloud_path"]).write_bytes(b"pre-existing")
    with pytest.raises(WorkerRequestError, match="output path already exists"):
        read_worker_request(path)
