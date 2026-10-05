# PL-0338 - Codex Prompt V01

Task: **Audit trail for asset metadata edits**
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

Implement an append-only integrity-chained Packaging Library audit trail for metadata mutations.

Each edit event must record deterministic event ID/digest, prior event digest, library state revision, actor ID, UTC timestamp, reason, operation type, target entity IDs, before/after revision IDs and a bounded list of changed field names. Do not embed attachment bytes, supplier secrets or ambient paths.

Library mutation APIs must require an expected state revision and append exactly one valid audit event atomically with the new canonical library state. Replay/validation must detect truncation, reorder, digest tampering, stale edits and disconnected history.

## Handoff

Publish implementation/evidence commit(s), then publish `coordination/sessions/M15-C001/PL-0338_CODEX_LOG_V01.md` separately. Record changed files, validation, limitations and parity.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
