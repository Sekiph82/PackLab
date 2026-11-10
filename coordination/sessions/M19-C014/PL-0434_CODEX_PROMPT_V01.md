# PL-0434 Codex Prompt V01 — Packaging Technical Dossier Export

Date: 2026-10-22  
Owner authorization: delegated autonomous PackLab implementation and queue sequencing.

## Objective

Add an explicit, offline export API that produces a single-page, machine-readable PDF dossier for one supplied immutable Packaging Asset V1 revision.

## Allowed scope

- Add a backend-neutral export record/manifest and Qt PDF rendering under `core/src/packlab_core/`.
- Add focused synthetic tests under `tests/core/`.
- Use the already installed PySide6 Qt PDF APIs; no dependency changes, external executables, network access, or native builds.
- Update root `TASKS.md`, this session's validation criteria and Codex log, and `project-control/codex/jobs/PL-0434/job.json`.

## Hard constraints

- Accept exactly one validated immutable `PackagingAsset`; preserve its asset ID, content-derived revision ID, exact measurements/units, and every canonical data field's recorded provenance classification.
- Include an explicit visible disclaimer that the document is packaging metadata only and does not establish physical accuracy, supplier certification, compliance, or manufacturing authorization.
- Keep PDF bytes in memory and return them to the caller. Do not select or write a filesystem path, access a live store, resolve project paths, read linked source bytes, or include local paths/secrets.
- Use a deterministic field ordering and stable manifest contract; report SHA-256 of the PDF and canonical source JSON. Reject invalid/mismatched source identity and fail closed when Qt PDF capability or parsing/render smoke is unavailable.
- Zero Actions/paid CI, no PR/source push to `main`, no OCCT/OCP or Installer build. Preserve owner changes and unrelated caches/worktrees.

## Validation and handoff

Run the focused synthetic core tests with the existing `.venv`, targeted Ruff and `git diff --check`. Confirm one-page PDF parse/render and source identity/provenance/disclaimer in assertions. Record exact results, privacy, limitations and publication state. Continue with the next dependency-ready task after local completion unless a genuine gate exists.
