# PL-0344 - Codex Prompt V01

Task: **Create new SKU from existing geometry**
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

Implement a Create new SKU from existing geometry workflow in the Library.

The workflow selects an existing Packaging Asset geometry, creates a new immutable Packaging SKU revision with user-entered SKU ID/name/status and optional accepted artwork/Label Zone assignment references, and links it to the existing asset/Design Model preference without copying or altering geometry.

UI must preview the source geometry/asset identity being reused, validate SKU ID uniqueness, show supplier/estimate provenance without cloning it as new SKU factual authority, and commit through the accepted library service/audit trail. Cancel leaves no partial state.

## Handoff

Publish implementation/evidence commit(s), then publish `coordination/sessions/M15-C001/PL-0344_CODEX_LOG_V01.md` separately. Record changed files, validation, limitations and final parity.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
