# PL-0433 Codex Prompt V01 — Alternative Packaging Supplier Comparison

Date: 2026-10-22  
Owner authorization: delegated autonomous PackLab implementation and queue sequencing.

## Objective

Add an in-memory Studio comparison component for multiple exact immutable Packaging Asset revisions, preserving supplier identity, field-level provenance, and unknown values without ranking suppliers or recommending a purchase.

## Allowed scope

- Add a backend-neutral comparison report and a small Qt presentation under `apps/windows-studio/src/packlab_studio/`.
- Add focused synthetic tests under `tests/studio/`.
- Update root `TASKS.md`, this session's validation criteria and Codex log, and `project-control/codex/jobs/PL-0433/job.json`.
- No file export is needed for this bounded task.

## Hard constraints

- Require at least two distinct immutable `PackagingAsset` revisions and retain exact asset IDs/revision IDs. Show supplier name and ID only when explicitly present; preserve missing supplier identity as unknown.
- Compare only fields already present in the supplied records: packaging family, volume, height, body diameter, weight, base material, closure, and status. Preserve missing values as `UNKNOWN`; do not fill, convert across incompatible units, score, rank, normalize a winner, or invent a supplier recommendation.
- Include each field's exact provenance classification next to the source value. The report is descriptive and non-authoritative; it does not establish supplier eligibility, compliance, quality, availability, price, or commercial suitability.
- Keep the data in memory. Do not access live supplier/SKU stores, private files, artwork bytes, network services, AI/model outputs, or write report artifacts.
- Zero Actions/paid CI, no PR, no source push to `main`, no native OCCT/OCP, no Installer build. Preserve owner changes and unrelated caches/worktrees.

## Validation and handoff

Run the focused synthetic Studio test module with the existing `.venv`, targeted Ruff, and `git diff --check`. Record exact results, failures/fixes, privacy, limitations, and publication state in `PL-0433_CODEX_LOG_V01.md`. Continue with the next dependency-ready task after local completion unless a genuine gate exists.
