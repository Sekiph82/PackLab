from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

try:
    import safetensors.torch as safetensors_torch
    import torch
    from safetensors.torch import save_file
except ImportError:
    safetensors_torch = None
    torch = None
    save_file = None

from packlab_core.vggt_checkpoint import (
    VGGTCheckpointLoadError,
    load_safetensors_into_cpu_model,
)


def identity(path: Path) -> tuple[int, str]:
    data = path.read_bytes()
    return len(data), hashlib.sha256(data).hexdigest()


@unittest.skipIf(torch is None, "isolated VGGT CPU runtime dependencies are unavailable")
class StreamingCheckpointLoaderTests(unittest.TestCase):
    def test_loads_tiny_synthetic_state_on_cpu_without_load_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            checkpoint = Path(temporary) / "synthetic.safetensors"
            source = torch.nn.Linear(3, 2, bias=True)
            save_file(
                {key: value.detach().contiguous() for key, value in source.state_dict().items()},
                checkpoint,
            )
            expected_size, expected_digest = identity(checkpoint)
            target = torch.nn.Linear(3, 2, bias=True)

            def forbidden_load_file(*args, **kwargs):
                raise AssertionError("full state-dictionary load is forbidden")

            with patch.object(safetensors_torch, "load_file", forbidden_load_file):
                result = load_safetensors_into_cpu_model(
                    target,
                    checkpoint,
                    expected_size_bytes=expected_size,
                    expected_sha256=expected_digest,
                )

            self.assertEqual(result.sha256, expected_digest)
            self.assertEqual(result.tensor_count, 2)
            for key, value in source.state_dict().items():
                torch.testing.assert_close(target.state_dict()[key], value)
            self.assertTrue(
                all(value.device.type == "cpu" for value in target.state_dict().values())
            )

    def test_wrong_digest_fails_before_model_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            checkpoint = Path(temporary) / "synthetic.safetensors"
            source = torch.nn.Linear(3, 2, bias=True)
            save_file(
                {key: value.detach().contiguous() for key, value in source.state_dict().items()},
                checkpoint,
            )
            expected_size, _ = identity(checkpoint)
            target = torch.nn.Linear(3, 2, bias=True)
            before = {key: value.detach().clone() for key, value in target.state_dict().items()}

            with self.assertRaisesRegex(VGGTCheckpointLoadError, "digest does not match"):
                load_safetensors_into_cpu_model(
                    target,
                    checkpoint,
                    expected_size_bytes=expected_size,
                    expected_sha256="0" * 64,
                )

            for key, value in target.state_dict().items():
                torch.testing.assert_close(value, before[key])

    def test_mismatched_keys_fail_before_tensor_copy(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            checkpoint = Path(temporary) / "synthetic.safetensors"
            save_file({"unexpected": torch.zeros(1)}, checkpoint)
            expected_size, expected_digest = identity(checkpoint)
            target = torch.nn.Linear(3, 2, bias=True)
            before = {key: value.detach().clone() for key, value in target.state_dict().items()}

            with self.assertRaisesRegex(VGGTCheckpointLoadError, "tensor keys do not match"):
                load_safetensors_into_cpu_model(
                    target,
                    checkpoint,
                    expected_size_bytes=expected_size,
                    expected_sha256=expected_digest,
                )

            for key, value in target.state_dict().items():
                torch.testing.assert_close(value, before[key])

    def test_wrong_size_and_symlink_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            checkpoint = root / "synthetic.safetensors"
            save_file({"weight": torch.ones(2)}, checkpoint)
            expected_size, expected_digest = identity(checkpoint)
            model = torch.nn.Linear(1, 2, bias=False)
            with self.assertRaisesRegex(VGGTCheckpointLoadError, "metadata does not match"):
                load_safetensors_into_cpu_model(
                    model,
                    checkpoint,
                    expected_size_bytes=expected_size + 1,
                    expected_sha256=expected_digest,
                )

            alias = root / "alias.safetensors"
            try:
                alias.symlink_to(checkpoint)
            except (OSError, NotImplementedError):
                self.skipTest("symlink creation is unavailable in this Windows environment")
            with self.assertRaisesRegex(VGGTCheckpointLoadError, "metadata does not match"):
                load_safetensors_into_cpu_model(
                    model,
                    alias,
                    expected_size_bytes=expected_size,
                    expected_sha256=expected_digest,
                )

    def test_shape_mismatch_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            checkpoint = Path(temporary) / "synthetic.safetensors"
            source = torch.nn.Linear(3, 2, bias=True)
            save_file(
                {key: value.detach().contiguous() for key, value in source.state_dict().items()},
                checkpoint,
            )
            expected_size, expected_digest = identity(checkpoint)
            target = torch.nn.Linear(4, 2, bias=True)

            with self.assertRaisesRegex(VGGTCheckpointLoadError, "shape or dtype differs"):
                load_safetensors_into_cpu_model(
                    target,
                    checkpoint,
                    expected_size_bytes=expected_size,
                    expected_sha256=expected_digest,
                )

    def test_dtype_mismatch_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            checkpoint = Path(temporary) / "synthetic.safetensors"
            source = torch.nn.Linear(3, 2, bias=True)
            save_file(
                {key: value.detach().contiguous() for key, value in source.state_dict().items()},
                checkpoint,
            )
            expected_size, expected_digest = identity(checkpoint)
            target = torch.nn.Linear(3, 2, bias=True).double()

            with self.assertRaisesRegex(VGGTCheckpointLoadError, "shape or dtype differs"):
                load_safetensors_into_cpu_model(
                    target,
                    checkpoint,
                    expected_size_bytes=expected_size,
                    expected_sha256=expected_digest,
                )


if __name__ == "__main__":
    unittest.main()
