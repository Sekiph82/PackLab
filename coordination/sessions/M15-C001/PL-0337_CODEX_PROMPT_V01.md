# PL-0337 - Codex Prompt V01

Task: **Supplier drawings, quotations and notes attachments**
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

Implement a Studio-level Packaging Library store with an explicitly supplied local library root and content-addressed attachment storage.

Attachments are opaque local evidence for supplier drawings, quotations and notes. Copy accepted bytes into the library store under digest-derived project-independent relative paths. Canonical attachment records must include stable attachment ID, SHA-256, byte length, media/display metadata, attachment role, optional related asset/component/SKU IDs and relative storage path. Never persist the original absolute source path.

Reject symlinks, traversal, empty/oversized inputs and executable/script processing. Do not parse or execute supplier documents. Use bounded streaming/copy and atomic publication. Attachment bytes must not be committed to the PackLab Git repository by implementation/tests.

## Handoff

Publish implementation/evidence commit(s), then publish `coordination/sessions/M15-C001/PL-0337_CODEX_LOG_V01.md` separately. Record changed files, validation, limitations and parity.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
