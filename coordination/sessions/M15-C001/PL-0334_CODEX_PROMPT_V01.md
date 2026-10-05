# PL-0334 - Codex Prompt V01

Task: **Link scans, Scan Master and Design Models**
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

Implement exact geometry/revision linkage from one Packaging Asset to raw Scan(s), at most one promoted Scan Master, and multiple Design Model revisions.

Links must use exact PackLab project_id plus stable source revision/asset IDs and available digests/authority metadata. Raw-scan links may be plural. The promoted Scan Master link is zero-or-one. Design Model links are ordered/deduplicated immutable references and may include active/preferred presentation metadata without replacing source authority.

Do not copy geometry into the library and do not persist ambient project-root absolute paths. Runtime project-root resolution belongs to the Studio layer and must be injected.

## Handoff

Publish implementation/evidence commit(s), then publish `coordination/sessions/M15-C001/PL-0334_CODEX_LOG_V01.md` as a separate log-only commit. Record changed files, commands/results, limitations and final parity.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
