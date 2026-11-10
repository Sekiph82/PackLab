# PL-0435 Codex Prompt V01 — Offline Visual Reference Boundary

Date: 2026-10-22  
Owner authorization: direct owner instruction to continue autonomous PackLab development and the PL-0435 reprioritization recorded in root `TASKS.md`.

## Objective

Implement a small backend-neutral provenance and record contract for an optional AI Visual Reference lane. Keep the reference explicitly generated and non-authoritative. This is local/offline implementation only.

## Mandatory pre-read

Read and follow `docs/implementation/PL-0435_AI_VISUAL_REFERENCE_LANE.md` in full. Its measurement, Scan Master, capture coverage, calibration, export-authority, and license boundaries are binding.

## Allowed scope

- Add a backend-neutral record/request/provenance contract in `core/src/packlab_core/visual_reference.py`.
- Add focused local tests in `tests/core/test_visual_reference.py`.
- Add an isolated viewport scene kind with per-object visibility, persistent generated/caveat labeling, and preview-sidecar metadata in `apps/windows-studio/src/packlab_studio/viewport.py` and `viewport_export.py`.
- Add focused UI-contract tests in `tests/studio/test_visual_reference_viewport.py`.
- Update the live tracker and autonomy/policy docs as explicitly authorized by the owner.
- Write this cycle's matching validation criteria and Codex log.

## Hard constraints

- No model implementation, download, inference, SDK dependency, checkpoint, or model enablement. Licensing and pinned checkpoint evidence are not available yet.
- No generated artifact may become Scan Master, measurement/calibration input, capture coverage, or authoritative engineering geometry.
- No changes to `TASKS.md` acceptance claims for PL-0354. It remains blocked/not run; never claim iOS XCTest ran on Windows.
- Zero GitHub Actions and paid CI. No PR and no source push to `main`; do not run native OCCT/OCP/Installer builds.
- Preserve owner Desktop/OwnerDev data. No destructive cleanup.
- Historical prompts, logs, audits, and reviewer verdicts are immutable evidence; do not rewrite them.

## Validation and handoff

Run only the focused local tests stated in `VALIDATION_CRITERIA_V01.md`, plus `git diff --check`. Record exact results, local-only status, and any task-owned temporary-file cleanup in `CODEX_LOG_V01.md`. Continue the autonomous PackLab queue after recording the actual state; do not wait for a routine audit turn.
