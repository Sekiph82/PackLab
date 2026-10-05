# PL-0332 - Codex Prompt V01

Task: **Define Packaging Asset schema**
Milestone: **M15 - Kenya Packaging Library**
Cycle: **M15-C001**

## M15 global rules

- Read live root TASKS.md, M14 final audit, M13 final audit, M09 physical-validation deferral, ADR-0005, and the exact predecessor prompt/criteria before implementation.
- Root TASKS.md lifecycle is ChatGPT-owned; Codex must not edit it.
- M15 Library is a Studio-level portable packaging library. Browsing must not require an open PackLab project.
- Canonical library identities and documents must never depend on ambient absolute paths, usernames, machine identity or network access.
- Links back to PackLab projects must use exact project/revision/digest identifiers; runtime project-root resolution is injected separately and must not rewrite canonical identity.
- Supplier factual metadata and PackLab-estimated metadata must never be silently merged or promoted.
- Existing Design Model, Scan Master, artwork, material and M14 render artifacts remain source authority; M15 stores links/metadata and must not mutate them.
- Existing M09 physical-validation deferrals and all non-manufacturing/non-certification limits remain in force.
- No new network/runtime download, hidden cloud dependency, secret/private evidence, unreviewed dependency or executable attachment processing.
- Every child gets implementation/evidence commit(s), then a distinct child-log-only commit ending exactly READY_FOR_INDEPENDENT_AUDIT.
- Run focused/predecessor tests, locked full suite, changed-file Ruff/format, targeted mypy/compile where applicable, dependency/lockfile, privacy/security/scope and remote parity checks.
- M16+ is unauthorized.

## Required implementation

Implement a new immutable deterministic Packaging Asset domain contract for the Kenya Packaging Library.

Required fields must include stable internal asset ID, display/name, packaging family, nominal volume, supplier identity/name, base material, empty package weight, neck/closure metadata and lifecycle/status metadata needed by later filters. Unknown values must be explicitly representable; do not fabricate defaults.

Use bounded typed values and explicit units for numeric dimensions/volume/weight. The record must be serializable deterministically with a content-derived revision ID. It must contain no project root, absolute path, artwork bytes, geometry bytes or supplier-certification inference.

Design the contract so PL-0333 can add field-level provenance without breaking factual/estimated separation.

## Handoff

Publish implementation/evidence commit(s), then publish `coordination/sessions/M15-C001/PL-0332_CODEX_LOG_V01.md` as a separate log-only commit. Record changed files, commands/results, limitations and final parity.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
