# PL-0436 Codex Log V07 — Verified Streaming Checkpoint Loader

> Privacy redaction (2026-11-04): machine-specific absolute checkout/TEMP paths in this log were replaced with generic labels; command results and measured values are unchanged. See PL-0436_LOG_PATH_REDACTION_ADDENDUM_V01.md.


Date: 2026-10-23 (Europe/Istanbul)

## Starting state and authority

- Starting and final source commit: `f8745047063aca6c17378ecb33604e6e1e5b5f02`; no commit created.
- Checkout: `[owner-specific PackLab Desktop path redacted]`, branch `main`. `git fetch origin main` succeeded; `HEAD == origin/main`, ahead/behind `0/0`. Extensive pre-existing tracked/untracked PackLab changes remained; none were reset, stashed, cleaned, checked out, or overwritten.
- Active prompt/criteria: `PL-0436_CODEX_PROMPT_V07.md` and `PL-0436_VALIDATION_CRITERIA_V07.md`. The mandatory `PL-0436_COMMERCIAL_NEURAL_RECONSTRUCTION_RESEARCH.md` pre-read was re-read; V06 source and evidence were reviewed.
- Owner VGGT/Hugging Face access and local checkpoint-use approval remain complete. No repeat approval was requested.

## Implementation

- Added `core/src/packlab_core/vggt_checkpoint.py`, a lazy-import, strict CPU safetensors loader. It rejects non-regular/reparse paths and wrong size, hashes the pinned file before importing model libraries, verifies exact state-key sets, and copies one tensor at a time instead of constructing the complete checkpoint dictionary with `safetensors.torch.load_file`.
- It checks tensor shape/dtype/device and compares file identity metadata again after the load. Error text excludes local paths and upstream exception detail. If a tensor fails after earlier tensors were copied, callers must discard that newly constructed model; loading is not transactional.
- Added tiny synthetic `torch.nn.Linear` tests using generated safetensors only: successful exact copy, forbidden full-dictionary loader, digest/size/key/shape/dtype rejection, CPU-only tensors and symlink protection. No real checkpoint or VGGT model was opened, instantiated or executed.

## Validation

1. Command: `git fetch origin main; git rev-list --left-right --count HEAD...origin/main`
   - Expected: safe synchronization and no divergence.
   - Actual: fetch succeeded; `0 0`.
2. Command: `$env:PYTHONPATH=(Resolve-Path core/src).Path; $env:LOCALAPPDATA\PackLab\venvs\vggt-cpu\Scripts\python.exe -B tests/core/test_vggt_checkpoint.py`
   - Expected: all tiny synthetic loader cases pass in the isolated runtime with no checkpoint/model use.
   - Actual: **6 tests ran, 1 skipped**, all remaining tests passed. Symlink creation is unavailable in this Windows environment.
3. Command: `\.venv\Scripts\python.exe -B -m pytest -q tests/core/test_vggt_checkpoint.py tests/core/test_neural_reconstruction_runtime.py tests/core/test_neural_reconstruction_io.py tests/core/test_neural_reconstruction_backend.py`
   - Expected: focused regression suites pass; the isolated loader module skips in the PackLab venv because torch/safetensors are intentionally installed only in the separate runtime.
   - Actual: **42 passed, 8 skipped**; 6 synthetic loader cases skipped in the PackLab venv, and 2 symlink cases require Windows symlink creation unavailable.
4. Command: `\.venv\Scripts\ruff.exe check core/src/packlab_core/vggt_checkpoint.py core/src/packlab_core/neural_reconstruction_runtime.py tests/core/test_vggt_checkpoint.py tests/core/test_neural_reconstruction_runtime.py tests/core/test_neural_reconstruction_io.py tests/core/test_neural_reconstruction_backend.py`
   - Expected: no diagnostics.
   - Actual: **All checks passed**. An initial I001 import-order diagnostic was corrected. The isolated runtime does not include pytest, so the synthetic tests use Python's standard `unittest` runner; no dependency was installed.
5. Command: `\.venv\Scripts\python.exe -B -c "import sys; import packlab_core.vggt_checkpoint; assert 'torch' not in sys.modules; print('lazy import passed')"`
   - Expected: importing the helper does not import torch.
   - Actual: `lazy import passed` (exit 0).
6. Command: `git diff --check`
   - Expected: no whitespace errors.
   - Actual: exit 0; only existing LF-to-CRLF working-copy warnings were reported for unrelated dirty files.

## Limits, privacy, and handoff

- This is a streaming checkpoint loader seam, not a concrete end-to-end VGGT inference engine. The latest live available-RAM sample was 1,517,174,784 bytes, below the 5,026,367,224-byte checkpoint, so real inference remains blocked and was not attempted.
- No checkpoint bytes were read, no VGGT model was instantiated, no inference or download was performed, and no additional packages were installed. The V07 tests used only tiny generated synthetic weights.
- Owner access/local-use approval is complete. Resolved dependency notices and end-user AUP/license presentation remain packaging work before distribution, not pending owner access approval.
- Zero Actions/paid CI; no PR; no source push to `main`; no native OCCT/OCP or Installer build. `NO_LOCAL_WORKTREE_CREATED`; no dashboard used. No credentials or private data were added. No independent review, hosted verification, physical acceptance or release-readiness claim.

`LOCAL_PINNED_CPU_STREAMING_LOADER_IMPLEMENTED_AND_SYNTHETICALLY_TESTED_OWNER_ACCESS_APPROVED_REAL_INFERENCE_PENDING_CONCRETE_ENGINE_AND_SUFFICIENT_AVAILABLE_RAM_NO_RELEASE_CLAIM`
