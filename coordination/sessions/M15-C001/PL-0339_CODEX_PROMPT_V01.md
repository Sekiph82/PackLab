# PL-0339 - Codex Prompt V01

Task: **Grid/list Packaging Library browser**
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

Replace the existing Route.LIBRARY placeholder with a real PySide6 Packaging Library browser backed by the accepted library store/service.

Implement deterministic grid/list modes, asset selection, thumbnail cells, empty/loading/error states and project-independent browsing. Use an injected library service/root rather than requiring an open ProjectManager project. Thumbnail references must be digest-bound local library/project evidence; missing thumbnails show a deterministic placeholder, never a remote fetch.

Keep canonical domain logic outside widgets. Add headless Qt tests for route wiring, mode toggle, selection stability, refresh and malformed/missing thumbnail behavior.

## Handoff

Publish implementation/evidence commit(s), then publish `coordination/sessions/M15-C001/PL-0339_CODEX_LOG_V01.md` separately. Record changed files, validation, limitations and parity.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
