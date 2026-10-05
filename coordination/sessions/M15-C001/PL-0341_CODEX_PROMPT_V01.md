# PL-0341 - Codex Prompt V01

Task: **Filters for volume, material, closure and status**
Milestone: **M15 - Kenya Packaging Library**
Cycle: **M15-C001**

## M15 global rules

- Read live root TASKS.md, M14 final audit, M13 final audit, M09 physical-validation deferral, ADR-0005, and exact predecessor prompt/criteria before implementation.
- Root TASKS.md lifecycle is ChatGPT-owned; Codex must not edit it.
- M15 Library is a Studio-level portable packaging library. Browsing must not require an open PackLab project.
- Canonical identities/documents must not depend on ambient absolute paths, usernames, machine identity or network access.
- Runtime project-root/library-root paths are injected and excluded from canonical identity.
- Supplier facts, user declarations and PackLab estimates remain explicitly separate.
- Existing PackLab project/revision/artwork/material/render authority is linked, never mutated.
- No runtime network/download, hidden cloud dependency, secret/private evidence, unreviewed dependency or executable attachment processing.
- Every child gets implementation/evidence commit(s), then distinct child-log-only commit ending exactly READY_FOR_INDEPENDENT_AUDIT.
- Run focused/predecessor tests, locked full suite, Ruff/format, targeted mypy/compile where applicable, dependency/lockfile, privacy/security/scope and remote parity checks.
- M16+ is unauthorized.

## Required implementation

Add deterministic composable filters for nominal volume, material, closure metadata and lifecycle/status and integrate them with PL-0340 search.

Volume filtering must respect explicit units and unknown values; no hidden unit guess. Material/closure/status filters use canonical normalized metadata/provenance-aware values. Multiple active filters combine with logical AND, while values within one multi-select dimension combine with OR unless the UI explicitly presents a single-select.

Provide clear/reset behavior and stable result ordering. Unknown/unset values must be filterable or explicitly excluded according to selected policy, never coerced to zero/empty factual values.

## Handoff

Publish implementation/evidence commit(s), then publish `coordination/sessions/M15-C001/PL-0341_CODEX_LOG_V01.md` separately. Record changed files, validation, limitations and parity.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
