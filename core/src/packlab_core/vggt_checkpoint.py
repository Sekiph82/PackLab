"""Strict CPU streaming loader for a locally pinned VGGT safetensors file.

This module does not import model libraries until a caller requests loading.
It deliberately avoids ``safetensors.torch.load_file`` so a full checkpoint
state dictionary is not retained alongside the model parameters.
"""

from __future__ import annotations

import hashlib
import re
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_CHUNK_BYTES = 1024 * 1024


class VGGTCheckpointLoadError(RuntimeError):
    """Checkpoint validation or streaming load failed without local path detail."""


@dataclass(frozen=True, slots=True)
class VGGTCheckpointLoadResult:
    sha256: str
    tensor_count: int


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(_CHUNK_BYTES), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_safetensors_into_cpu_model(
    model: Any,
    checkpoint_path: str | Path,
    *,
    expected_size_bytes: int,
    expected_sha256: str,
) -> VGGTCheckpointLoadResult:
    """Validate a pinned checkpoint, then copy one CPU tensor at a time.

    The caller must pass a newly constructed model and discard it if this
    function raises after copying starts. This function is not a transactional
    rollback mechanism for an existing live model.
    """

    if (
        isinstance(expected_size_bytes, bool)
        or not isinstance(expected_size_bytes, int)
        or expected_size_bytes <= 0
        or not isinstance(expected_sha256, str)
        or _SHA256.fullmatch(expected_sha256) is None
    ):
        raise ValueError("expected checkpoint identity is invalid")

    path = Path(checkpoint_path)
    try:
        before = path.lstat()
    except OSError as error:
        raise VGGTCheckpointLoadError("pinned VGGT checkpoint is unavailable") from error
    attributes = getattr(before, "st_file_attributes", 0)
    reparse_mask = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    if (
        not stat.S_ISREG(before.st_mode)
        or (reparse_mask and attributes & reparse_mask)
        or before.st_size != expected_size_bytes
    ):
        raise VGGTCheckpointLoadError("pinned VGGT checkpoint metadata does not match")

    try:
        observed_sha256 = _sha256_file(path)
    except OSError as error:
        raise VGGTCheckpointLoadError("pinned VGGT checkpoint could not be verified") from error
    if observed_sha256 != expected_sha256:
        raise VGGTCheckpointLoadError("pinned VGGT checkpoint digest does not match")

    try:
        import torch
        from safetensors import safe_open
    except ImportError as error:
        raise VGGTCheckpointLoadError("CPU safetensors runtime is unavailable") from error

    try:
        model_state = model.state_dict()
        if not hasattr(model_state, "keys"):
            raise VGGTCheckpointLoadError("VGGT model state is invalid")
        model_keys = set(model_state.keys())
        with safe_open(path, framework="pt", device="cpu") as checkpoint:
            checkpoint_keys = set(checkpoint.keys())
            if model_keys != checkpoint_keys:
                raise VGGTCheckpointLoadError("VGGT checkpoint tensor keys do not match the model")

            with torch.no_grad():
                for name, target in model_state.items():
                    if not isinstance(target, torch.Tensor) or target.device.type != "cpu":
                        raise VGGTCheckpointLoadError("VGGT model tensors must remain on CPU")
                    source = checkpoint.get_tensor(name)
                    if (
                        not isinstance(source, torch.Tensor)
                        or source.device.type != "cpu"
                        or source.shape != target.shape
                        or source.dtype != target.dtype
                    ):
                        raise VGGTCheckpointLoadError(
                            "VGGT checkpoint tensor shape or dtype differs"
                        )
                    target.copy_(source)
                    del source
    except VGGTCheckpointLoadError:
        raise
    except Exception as error:
        raise VGGTCheckpointLoadError("VGGT checkpoint streaming load failed") from error

    try:
        after = path.lstat()
    except OSError as error:
        raise VGGTCheckpointLoadError("pinned VGGT checkpoint changed during loading") from error
    after_attributes = getattr(after, "st_file_attributes", 0)
    if (
        not stat.S_ISREG(after.st_mode)
        or (reparse_mask and after_attributes & reparse_mask)
        or (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
        != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    ):
        raise VGGTCheckpointLoadError("pinned VGGT checkpoint changed during loading")

    return VGGTCheckpointLoadResult(observed_sha256, len(model_keys))
