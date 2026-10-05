# PL-0345 - Codex Prompt V01

Task: **Library backup/export and restore validation**
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

Implement a portable offline Packaging Library backup/export and restore-validation format using only reviewed existing/standard-library capabilities.

Backup must contain a versioned canonical manifest, canonical library state/audit history, content-addressed attachments and thumbnails required for portability, each with byte length/SHA-256. Use safe relative POSIX paths and deterministic manifest ordering.

Restore must support validate-only and atomic restore into an empty/new library root. Reject path traversal, absolute paths, symlinks, duplicate archive names, unsupported schema/version, missing/extra required files, digest/length mismatch, corrupted audit chain and oversized archive budgets. Do not overwrite an existing nonempty library by default and do not fetch missing files from network.

## Handoff

Publish implementation/evidence commit(s), then publish `coordination/sessions/M15-C001/PL-0345_CODEX_LOG_V01.md` separately. Record changed files, validation, limitations and final parity.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
