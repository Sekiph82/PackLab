from __future__ import annotations

from pathlib import Path

import pytest

from packlab_core.neural_reconstruction import VGGTWorkspaceInference
from packlab_core.neural_reconstruction_io import VGGTResolvedImage
from packlab_core.neural_reconstruction_runtime import (
    GuardedVGGTWorkspaceEngine,
    LazyGuardedVGGTWorkspaceEngine,
    VGGTMemoryAdmissionError,
    VGGTMemoryBudget,
    VGGTMemorySnapshot,
)
from packlab_core.reconstruction import CancelToken


class FakeMemoryReader:
    def __init__(self, available: int = 100, total: int = 200, error: Exception | None = None):
        self.available = available
        self.total = total
        self.error = error
        self.calls = 0

    def snapshot(self) -> VGGTMemorySnapshot:
        self.calls += 1
        if self.error is not None:
            raise self.error
        return VGGTMemorySnapshot(self.total, self.available)


class FakeEngine:
    def __init__(self):
        self.available_calls = 0
        self.infer_calls = 0
        self.images = ()
        self.result = VGGTWorkspaceInference("r1", (), (), point_count=0)

    def available(self) -> bool:
        self.available_calls += 1
        return True

    def infer(self, images, cancel) -> VGGTWorkspaceInference:
        self.infer_calls += 1
        self.images = images
        return self.result


@pytest.mark.parametrize(
    ("total", "available"),
    ((0, 1), (100, 0), (-1, 2), (100, 101), (True, 1), (100, False)),
)
def test_memory_snapshot_rejects_invalid_values(total, available) -> None:
    with pytest.raises(ValueError):
        VGGTMemorySnapshot(total, available)


@pytest.mark.parametrize(
    ("checkpoint_bytes", "reserve_bytes"),
    ((0, 1), (1, 0), (-1, 1), (True, 1), (1, False)),
)
def test_memory_budget_rejects_invalid_values(checkpoint_bytes, reserve_bytes) -> None:
    with pytest.raises(ValueError):
        VGGTMemoryBudget(checkpoint_bytes, reserve_bytes)


def test_guarded_engine_rejects_insufficient_ram_before_engine_call(tmp_path: Path) -> None:
    checkpoint = tmp_path / "model.safetensors"
    checkpoint.write_bytes(b"0123456789")
    engine = FakeEngine()
    memory = FakeMemoryReader(available=19)
    guarded = GuardedVGGTWorkspaceEngine(
        engine,
        checkpoint,
        VGGTMemoryBudget(checkpoint_bytes=10, inference_reserve_bytes=10),
        memory,
    )

    assert not guarded.available()
    with pytest.raises(VGGTMemoryAdmissionError, match="insufficient available"):
        guarded.infer((), CancelToken())

    assert memory.calls == 2
    assert engine.available_calls == 0
    assert engine.infer_calls == 0


@pytest.mark.parametrize("checkpoint_state", ("missing", "wrong_size", "symlink"))
def test_guarded_engine_rejects_unverified_checkpoint_metadata_before_inference(
    tmp_path: Path, checkpoint_state: str
) -> None:
    checkpoint = tmp_path / "model.safetensors"
    if checkpoint_state == "wrong_size":
        checkpoint.write_bytes(b"wrong")
    elif checkpoint_state == "symlink":
        target = tmp_path / "target.safetensors"
        target.write_bytes(b"0123456789")
        try:
            checkpoint.symlink_to(target)
        except (OSError, NotImplementedError):
            pytest.skip("symlink creation is unavailable in this Windows environment")
    engine = FakeEngine()
    memory = FakeMemoryReader(available=100)
    guarded = GuardedVGGTWorkspaceEngine(
        engine,
        checkpoint,
        VGGTMemoryBudget(checkpoint_bytes=10, inference_reserve_bytes=10),
        memory,
    )

    with pytest.raises(VGGTMemoryAdmissionError, match="checkpoint"):
        guarded.infer((), CancelToken())
    assert memory.calls == 0
    assert engine.infer_calls == 0


def test_guarded_engine_rejects_memory_measurement_failure_before_inference(tmp_path: Path) -> None:
    checkpoint = tmp_path / "model.safetensors"
    checkpoint.write_bytes(b"0123456789")
    engine = FakeEngine()
    memory = FakeMemoryReader(error=OSError("synthetic memory reader failure"))
    guarded = GuardedVGGTWorkspaceEngine(
        engine,
        checkpoint,
        VGGTMemoryBudget(checkpoint_bytes=10, inference_reserve_bytes=10),
        memory,
    )

    with pytest.raises(VGGTMemoryAdmissionError, match="could not be measured"):
        guarded.infer((), CancelToken())
    assert engine.infer_calls == 0


def test_guarded_engine_delegates_after_metadata_and_ram_floor_pass(tmp_path: Path) -> None:
    checkpoint = tmp_path / "model.safetensors"
    checkpoint.write_bytes(b"0123456789")
    engine = FakeEngine()
    memory = FakeMemoryReader(available=21)
    image = VGGTResolvedImage("working/one.jpg", tmp_path / "one.jpg", "a" * 64, 1)
    guarded = GuardedVGGTWorkspaceEngine(
        engine,
        checkpoint,
        VGGTMemoryBudget(checkpoint_bytes=10, inference_reserve_bytes=10),
        memory,
    )

    assert guarded.available()
    result = guarded.infer((image,), CancelToken())

    assert result is engine.result
    assert engine.available_calls == 1
    assert engine.infer_calls == 1
    assert engine.images == (image,)


def test_lazy_guard_never_constructs_engine_before_ram_floor(tmp_path: Path) -> None:
    checkpoint = tmp_path / "model.safetensors"
    checkpoint.write_bytes(b"0123456789")
    engine = FakeEngine()
    factory_calls = []
    memory = FakeMemoryReader(available=19)
    guarded = LazyGuardedVGGTWorkspaceEngine(
        lambda: factory_calls.append(True) or engine,
        lambda: True,
        checkpoint,
        VGGTMemoryBudget(checkpoint_bytes=10, inference_reserve_bytes=10),
        memory,
    )

    assert not guarded.available()
    with pytest.raises(VGGTMemoryAdmissionError, match="insufficient available"):
        guarded.infer((), CancelToken())

    assert factory_calls == []
    assert engine.infer_calls == 0


def test_lazy_guard_constructs_once_after_admission_and_delegates(tmp_path: Path) -> None:
    checkpoint = tmp_path / "model.safetensors"
    checkpoint.write_bytes(b"0123456789")
    engine = FakeEngine()
    factory_calls = []
    memory = FakeMemoryReader(available=20)
    guarded = LazyGuardedVGGTWorkspaceEngine(
        lambda: factory_calls.append(True) or engine,
        lambda: True,
        checkpoint,
        VGGTMemoryBudget(checkpoint_bytes=10, inference_reserve_bytes=10),
        memory,
    )
    image = VGGTResolvedImage("working/one.jpg", tmp_path / "one.jpg", "a" * 64, 1)

    assert guarded.available()
    assert factory_calls == []
    guarded.infer((image,), CancelToken())
    guarded.infer((image,), CancelToken())

    assert factory_calls == [True]
    assert engine.infer_calls == 2
    assert engine.images == (image,)


def test_lazy_guard_does_not_construct_engine_after_cancellation(tmp_path: Path) -> None:
    checkpoint = tmp_path / "model.safetensors"
    checkpoint.write_bytes(b"0123456789")
    engine = FakeEngine()
    factory_calls = []
    memory = FakeMemoryReader(available=20)
    guarded = LazyGuardedVGGTWorkspaceEngine(
        lambda: factory_calls.append(True) or engine,
        lambda: True,
        checkpoint,
        VGGTMemoryBudget(checkpoint_bytes=10, inference_reserve_bytes=10),
        memory,
    )
    cancel = CancelToken()
    cancel.cancel()

    result = guarded.infer((), cancel)

    assert result.reconstruction_revision == "cancelled"
    assert factory_calls == []
    assert memory.calls == 0


def test_lazy_guard_uses_probe_without_constructing_engine(tmp_path: Path) -> None:
    checkpoint = tmp_path / "model.safetensors"
    checkpoint.write_bytes(b"0123456789")
    factory_calls = []
    probe_calls = []
    guarded = LazyGuardedVGGTWorkspaceEngine(
        lambda: factory_calls.append(True) or FakeEngine(),
        lambda: probe_calls.append(True) or False,
        checkpoint,
        VGGTMemoryBudget(checkpoint_bytes=10, inference_reserve_bytes=10),
        FakeMemoryReader(available=20),
    )

    assert not guarded.available()
    assert factory_calls == []
    assert probe_calls == [True]


def test_lazy_guard_rejects_inference_when_probe_reports_unavailable(tmp_path: Path) -> None:
    checkpoint = tmp_path / "model.safetensors"
    checkpoint.write_bytes(b"0123456789")
    factory_calls = []
    guarded = LazyGuardedVGGTWorkspaceEngine(
        lambda: factory_calls.append(True) or FakeEngine(),
        lambda: False,
        checkpoint,
        VGGTMemoryBudget(checkpoint_bytes=10, inference_reserve_bytes=10),
        FakeMemoryReader(available=20),
    )

    with pytest.raises(VGGTMemoryAdmissionError, match="prerequisites are unavailable"):
        guarded.infer((), CancelToken())
    assert factory_calls == []


@pytest.mark.parametrize(
    ("engine_factory", "message"),
    (
        (lambda: object(), "invalid engine"),
        (
            lambda: (_ for _ in ()).throw(RuntimeError("private local path")),
            "initialization failed",
        ),
    ),
)
def test_lazy_guard_rejects_invalid_or_failed_engine_factory_without_details(
    tmp_path: Path, engine_factory, message: str
) -> None:
    checkpoint = tmp_path / "model.safetensors"
    checkpoint.write_bytes(b"0123456789")
    guarded = LazyGuardedVGGTWorkspaceEngine(
        engine_factory,
        lambda: True,
        checkpoint,
        VGGTMemoryBudget(checkpoint_bytes=10, inference_reserve_bytes=10),
        FakeMemoryReader(available=20),
    )

    with pytest.raises(VGGTMemoryAdmissionError, match=message) as error:
        guarded.infer((), CancelToken())
    assert "private local path" not in str(error.value)


def test_worker_command_cannot_import_modules_planted_in_its_working_directory(
    tmp_path: Path,
) -> None:
    # Review P2 (PL-0436): `python -m` used to prepend the working directory, so a decoy
    # package there shadowed the pinned upstream code.
    import subprocess
    import sys

    from packlab_core.neural_reconstruction_runtime import _vggt_worker_command

    command = _vggt_worker_command(Path(sys.executable), tmp_path / "request.json")
    assert command[1:6] == ["-B", "-P", "-s", "-m", "packlab_core.vggt_worker"]
    (tmp_path / "packlab_decoy_probe.py").write_text("raise SystemExit(42)\n", encoding="utf-8")
    probe = [*command[:4], "-c", "import packlab_decoy_probe"]
    result = subprocess.run(probe, cwd=tmp_path, capture_output=True, check=False)
    assert result.returncode == 1 and b"ModuleNotFoundError" in result.stderr
    unprotected = subprocess.run(
        [sys.executable, "-B", "-c", "import packlab_decoy_probe"],
        cwd=tmp_path,
        capture_output=True,
        check=False,
    )
    assert unprotected.returncode == 42  # control: without -P the decoy is imported
