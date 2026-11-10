# PL-0436 Codex Prompt V07 — Verified Streaming Safetensors Load

Date: 2026-10-23  
Owner checkpoint access and local-use approval are complete. V07 reduces peak memory overhead in the future CPU engine by avoiding `safetensors.torch.load_file`, which materializes the complete state dictionary alongside model parameters.

## Objective

Add a strict CPU-only helper that verifies pinned checkpoint file metadata and SHA-256, then copies one safetensors tensor at a time into an already-created model. The helper must not use `load_file` or retain the full checkpoint state dictionary.

## Allowed scope

- Add `core/src/packlab_core/vggt_checkpoint.py` with metadata/hash validation and one-tensor-at-a-time CPU loading.
- Add synthetic tests using a tiny local `torch.nn.Module` and generated safetensors files in `tests/core/test_vggt_checkpoint.py`.
- Update this V07 prompt/criteria/log, root `TASKS.md`, and `project-control/codex/jobs/PL-0436/job.json`.

## Hard constraints

- Do not instantiate the actual VGGT model, open/read/load the real pinned checkpoint, perform inference, access Hugging Face, or download anything.
- Synthetic tests may use the already-installed isolated `vggt-cpu` environment; test tensors must remain tiny and temporary.
- Reject a symlink/non-regular file, wrong byte size, invalid/mismatched expected SHA-256, missing or extra state keys, non-CPU tensors, and shape/dtype mismatch.
- Import torch/safetensors lazily inside the loader. Never call `safetensors.torch.load_file` or construct a full checkpoint `state_dict`.
- Any partial model mutation after a synthetic tensor mismatch is acceptable only when the failed newly constructed model is discarded by the caller; document this boundary.
- Keep owner access/local-use approval complete. No Actions/paid CI, PR, push to `main`, native OCCT/OCP or Installer build. Preserve owner changes.

## Validation

Run the tiny synthetic loader tests under the isolated VGGT CPU Python environment, plus focused PackLab reconstruction tests and targeted Ruff where available. Validate job JSON/log SHA-256 and `git diff --check`. No model inference or full suite.
