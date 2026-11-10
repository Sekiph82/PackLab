# PL-0431 Codex Prompt V01 — Scan Master vs Design Model Review Mode

Date: 2026-10-22  
Owner authorization: delegated autonomous PackLab implementation and queue sequencing.

## Objective

Add an isolated Studio review component for viewing an immutable Scan Master and a Design Model preview side by side or as a ghosted overlay. Keep the two authorities distinct and bind the displayed identities to the exact revisions supplied by the caller.

## Allowed scope

- Add a backend-neutral review binding and a Qt raster comparison widget under `apps/windows-studio/src/packlab_studio/`.
- Add focused synthetic local tests under `tests/studio/`.
- Write this prompt, matching validation criteria and Codex log; update root `TASKS.md` and local job metadata after validation.
- Do not alter the existing app shell/navigation unless a safe existing injection point is identified without broad integration work.

## Hard constraints

- This is a review-only presentation. It must not modify either source revision, perform fitting/alignment, infer measurements, or authorize CAD/mold/export use.
- Display exact Scan Master and Design Model revision IDs and source geometry digests. Ghost mode is available only when the Design Model declares the exact Scan Master parent revision and geometry digest. Preserve a side-by-side path for standalone/unlinked models and label that relationship clearly.
- Do not accept AI visual references or generated geometry as either source. Do not add a model, checkpoint, inference runtime, network access, or auto-download.
- Do not invoke native OCCT/OCP, Installer, full-suite, GitHub Actions, paid CI, PR, or push source changes to `main`.
- Preserve existing owner changes and all worktree state; do not clean caches or unrelated files.

## Validation and handoff

Run the focused test module with the existing `.venv` only if the supported Python/PySide6 environment is available. Run `git diff --check`. Record exact results and limitations in `PL-0431_CODEX_LOG_V01.md`. If the current branch is `main`, leave implementation and log local; do not publish source changes to `main`. Mark integration or source-to-preview provenance limitations explicitly.
