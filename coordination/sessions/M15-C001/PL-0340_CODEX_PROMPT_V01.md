# PL-0340 - Codex Prompt V01

Task: **Search by ID, name, supplier and family**
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

Add deterministic normalized library search across Packaging Asset internal ID, display/name, supplier and package family.

Implement the query engine in a reusable non-widget service/domain layer and wire a search field into the Library view. Matching must be Unicode-safe casefolded text matching with bounded query length and stable result ordering. Empty query returns the unfiltered ordered asset set.

Search must operate only on locally loaded canonical metadata and never issue network requests or silently search attachment contents.

## Handoff

Publish implementation/evidence commit(s), then publish `coordination/sessions/M15-C001/PL-0340_CODEX_LOG_V01.md` separately. Record changed files, validation, limitations and parity.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
