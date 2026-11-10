# PL-0432 Codex Prompt V01 — POVU SKU Shelf-Lineup Visualization

Date: 2026-10-22  
Owner authorization: delegated autonomous PackLab implementation and queue sequencing.

## Objective

Add a reusable Studio component that lays out multiple exact POVU SKU revisions in one schematic shelf row using only the matching immutable Packaging Asset's provenance-backed overall height and body diameter.

## Allowed scope

- Add a pure lineup-plan module and Qt raster/widget presentation under `apps/windows-studio/src/packlab_studio/`.
- Add focused synthetic tests under `tests/studio/`.
- Update root `TASKS.md`, this session's validation criteria and Codex log, and `project-control/codex/jobs/PL-0432/job.json`.
- Update PackLab autonomous-operation instructions so queue work continues through dependency-ready tasks without requiring another routine prompt or heartbeat.

## Hard constraints

- Resolve every SKU to exactly the supplied immutable Packaging Asset ID/revision using the existing SKU validator. Require at least two and at most twelve distinct SKUs.
- Only accept height and body diameter with `mm` or `cm` units and existing non-UNKNOWN field provenance. Convert cm to mm without changing stored records. Reject missing/unsupported dimensions; never infer values from package family, image, label, mesh, AI, or neighboring SKU.
- The drawn shape is a schematic cylinder proxy, not product geometry, engineering CAD, shelf-fit certification, or physical measurement. Display revision IDs, dimension values/units, and provenance classifications.
- No artwork bytes, private supplier files, live SKU database, model/checkpoint, network, native OCCT/OCP, Installer, GitHub Actions, paid CI, PR, or source push to `main`.
- Preserve all existing owner changes and all unrelated caches/worktrees.

## Validation and handoff

Use only the existing `.venv` and focused synthetic test module. Run the named Ruff check and `git diff --check`. Record exact results, failures/fixes, privacy, limits, and publication state in `PL-0432_CODEX_LOG_V01.md`. Continue with the next dependency-ready PackLab task after this bounded implementation unless a genuine gate exists.
