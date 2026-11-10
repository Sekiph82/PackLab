# PL-0436 Codex Log V03 — VGGT Asset and Coordinate Bridge

> Privacy redaction (2026-11-04): machine-specific absolute checkout/TEMP paths in this log were replaced with generic labels; command results and measured values are unchanged. See PL-0436_LOG_PATH_REDACTION_ADDENDUM_V01.md.


Date: 2026-10-23 (Europe/Istanbul)

## Starting state and authority

- Starting/final source commit for this local implementation: `f8745047063aca6c17378ecb33604e6e1e5b5f02` (no commit created).
- Checkout: `[owner-specific PackLab Desktop path redacted]`, branch `main`; `HEAD` matched `origin/main` before work (`0/0` ahead/behind). The checkout already had extensive dirty PackLab work. No reset, stash, clean, checkout, or owner-change overwrite was performed.
- Active prompt and criteria: `PL-0436_CODEX_PROMPT_V03.md` and `PL-0436_VALIDATION_CRITERIA_V03.md`.
- Mandatory pre-read `docs/implementation/PL-0436_COMMERCIAL_NEURAL_RECONSTRUCTION_RESEARCH.md` was read in full. The local pinned VGGT source was inspected read-only for `load_and_preprocess_images_square`, OpenCV `cam-from-world` extrinsics, pixel intrinsics, and PackScan convention constants.
- Owner VGGT/Hugging Face access and local checkpoint-use approval are complete. They are not pending. This task did not access Hugging Face, download assets, or inspect/load/execute the checkpoint.

## Files changed for V03

- `core/src/packlab_core/neural_reconstruction_io.py` (new): ordered source-image resolver requiring exact per-asset source-manifest SHA-256 values; path containment, traversal/reparse rejection, stat-stability checks, and portable records without local paths; explicit square-padding/resizing transform; VGGT OpenCV world-to-camera to PackScan camera-to-world/world-point conversion and pixel-center intrinsic normalization; derived artifact publication with copy-time SHA-256, canonical manifest, authority/scale constraints, no overwrite, and task-owned staging cleanup.
- `tests/core/test_neural_reconstruction_io.py` (new): synthetic-only resolver, duplicate normalized IDs, digest/missing/traversal/reparse/mutation boundaries, source immutability, camera and point conversion, invalid transforms, derived manifest/path/authority checks, overwrite rejection, and staging cleanup.
- This log, V03 prompt/criteria, root `TASKS.md`, and `project-control/codex/jobs/PL-0436/job.json` record this task's state and evidence.

## Validation

1. Command: `.\.venv\Scripts\python.exe -B -m pytest -q tests/core/test_neural_reconstruction_io.py tests/core/test_neural_reconstruction_backend.py`
   - Expected: synthetic IO/coordinate tests and existing backend-contract tests pass without loading VGGT/checkpoint weights; nonzero exit is failure.
   - Actual: **15 passed, 1 skipped** (exit 0). The skipped symlink test reports that symlink creation is unavailable in this Windows environment. An earlier run exposed a mismatched expected error string for duplicate normalized IDs; the test expectation was corrected, and this final run passed.
2. Command: `.\.venv\Scripts\ruff.exe check core/src/packlab_core/neural_reconstruction_io.py tests/core/test_neural_reconstruction_io.py`
   - Expected: no lint diagnostics.
   - Actual: **All checks passed!** (exit 0).
3. Command: `git diff --check`
   - Expected: no whitespace errors.
   - Actual: exit 0. Git printed existing LF-to-CRLF working-copy warnings; no whitespace errors.

## Resource, safety, and limits

- Free physical RAM measured after the focused checks: **888,557,568 bytes** (about 847 MiB). This is insufficient for the 5,026,367,224-byte checkpoint plus runtime tensors. No checkpoint weights were read, loaded, or executed.
- Resolver and publisher have only synthetic test evidence. No PackScan parity, real image inference, visual output, physical ground truth, or metric scale is claimed.
- Runtime/deployment notice bundle and end-user AUP/license notice remain packaging work before distributing an enabled build; they are not a pending owner access/local-use approval.
- No GitHub Actions or paid CI; no PR; no commit or push; no native OCCT/OCP or Installer build. No worktree was created (`NO_LOCAL_WORKTREE_CREATED`). No dashboard was used.
- No credentials or private data were added. No independent review, hosted verification, physical acceptance, or release readiness is claimed.

## Handoff

`LOCAL_ASSET_RESOLVER_OUTPUT_WRITER_AND_COORDINATE_BRIDGE_COMPLETE_SYNTHETIC_TESTED_REAL_INFERENCE_PENDING_RUNTIME_WIRING_AND_SUFFICIENT_RAM_OWNER_ACCESS_APPROVAL_COMPLETE_NO_RELEASE_CLAIM` — the PackLab image asset and derived-output boundaries and explicit coordinate conversion are implemented and focused-tested. Owner access/local-use approval remains complete. Real inference still needs runtime wiring and adequate free RAM; this host currently has under 1 GiB free.
