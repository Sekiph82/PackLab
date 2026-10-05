# PL-0343 - Codex Prompt V01

Task: **Duplicate and variant relationship display**
Milestone: **M15 - Kenya Packaging Library**
Cycle: **M15-C001**

## M15 global rules

- Read live root TASKS.md, M14 final audit, M13 final audit, M09 physical-validation deferral, ADR-0005 and exact predecessor prompt/criteria before implementation.
- Root TASKS.md lifecycle is ChatGPT-owned; Codex must not edit it.
- Packaging Library is Studio-level, portable, local-first and usable without an open project.
- Canonical records use stable IDs/revisions/digests and safe relative paths only; runtime project/library roots are injected and excluded from canonical identity.
- Supplier facts, user declarations and PackLab estimates remain visibly/provenance-distinct.
- Existing project/Scan Master/Design Model/artwork/material/render artifacts are linked, never mutated.
- No network/runtime download, hidden cloud dependency, secret/private evidence, unreviewed dependency or executable attachment processing.
- Every child publishes implementation/evidence then separate log-only commit ending exactly READY_FOR_INDEPENDENT_AUDIT.
- Run focused/predecessor tests, locked full suite, Ruff/format, targeted mypy/compile as applicable, dependency/lockfile, privacy/security/scope and remote parity checks.
- M16+ is unauthorized.

## Required implementation

Add explicit Packaging Asset relationship records and display them on library cards/detail views.

Support at minimum DUPLICATE and VARIANT relationships. DUPLICATE must be symmetric and cannot self-link. VARIANT must identify a parent/base asset and variant asset and reject self-links/cycles. Relationship provenance/actor/reason must be explicit and revisioned; similarity alone must never auto-create a duplicate relationship.

Show relationship badges/sections and navigation between related assets without merging their metadata or revision histories.

## Handoff

Publish implementation/evidence commit(s), then publish `coordination/sessions/M15-C001/PL-0343_CODEX_LOG_V01.md` separately. Record changed files, validation, limitations and final parity.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
