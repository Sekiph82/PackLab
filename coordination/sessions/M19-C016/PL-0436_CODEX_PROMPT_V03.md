# PL-0436 Codex Prompt V03 — VGGT Asset and Coordinate Bridge

Date: 2026-10-23  
Owner authorization: continue VGGT work. Owner access and local checkpoint-use approval, authentication, pinned download and local SHA-256 are complete as recorded in V02. This V03 extends V02 only to the local input/output and coordinate bridge needed before inference. It does not ask for repeat VGGT/Hugging Face approval.

## Objective

Implement the PackLab-owned, model-independent boundary that resolves immutable source images for an injected VGGT runtime, normalizes VGGT OpenCV camera/world coordinates into PackScan conventions, and atomically publishes derived reconstruction artifacts without granting Scan Master or metric authority.

## Allowed scope

- Add `core/src/packlab_core/neural_reconstruction_io.py` with a read-only image resolver, explicit preprocessing transform, VGGT-to-PackScan camera/point conversion, and atomic derived-artifact publisher.
- Add focused synthetic-only tests in `tests/core/test_neural_reconstruction_io.py`.
- Update this session's V03 criteria/log, root `TASKS.md`, and `project-control/codex/jobs/PL-0436/job.json`.
- Reuse the pinned local VGGT source checkout for read-only coordinate-convention inspection; do not download additional assets.

## Hard constraints

- Never read, instantiate, or execute the checkpoint in this task. The current host has under 1 GiB free physical RAM; checkpoint inference remains unavailable until measured resource headroom is sufficient.
- No model host access or new downloads, no Hugging Face runtime dependency, no alternate model.
- Asset resolution must require exact source-manifest SHA-256 values, reject traversal/reparse escapes and changed files, preserve caller order, and never write to source assets.
- Output publication must reject overwrite/path escape/symlink destinations; outputs stay under a derived project path, retain source digest and `RECONSTRUCTION_OBSERVATION`, and reject `METRIC_VERIFIED`.
- Coordinate conversion must state the VGGT input pixel transform and camera/world conventions explicitly, use finite/shape checks, and never claim PackScan parity from synthetic tests alone.
- No Actions/paid CI, PR, source push to `main`, native OCCT/OCP or Installer build. Preserve all unrelated dirty owner changes.

## Validation

Run focused local tests for the new module and existing neural adapter contract, targeted Ruff, JSON/job-log hash validation, and `git diff --check`. No full suite or model inference.

