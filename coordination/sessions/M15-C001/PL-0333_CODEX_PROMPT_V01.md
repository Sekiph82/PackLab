# PL-0333 - Codex Prompt V01

Task: **Separate supplier facts from PackLab estimates**
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

Extend Packaging Asset metadata with field-level provenance that keeps supplier facts, user declarations and PackLab estimates semantically separate.

Define explicit provenance classes at minimum SUPPLIER_FACT, PACKLAB_ESTIMATE and USER_DECLARED/UNKNOWN. Supplier facts may carry an opaque source-reference ID/description; PackLab estimates must carry method/algorithm identity and may carry bounded confidence. A PackLab estimate must never serialize or display as a supplier fact or verified/certified value.

Provide deterministic edit/revision helpers that can change a field's value/provenance only by creating a new Packaging Asset revision. Preserve old revision immutability.

## Handoff

Publish implementation/evidence commit(s), then publish `coordination/sessions/M15-C001/PL-0333_CODEX_LOG_V01.md` as a separate log-only commit. Record changed files, commands/results, limitations and final parity.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
