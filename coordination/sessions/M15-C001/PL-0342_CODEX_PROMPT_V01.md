# PL-0342 - Codex Prompt V01

Task: **Asset detail page with 3D preview and revisions**
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

Implement a Packaging Asset detail view in the Library UI showing core metadata/provenance, linked scans/Scan Master/Design Model revisions, dimensions, reusable components and linked artworks/SKUs.

Add a 3D preview panel by reusing PackLab's existing QtRasterViewportAdapter/SceneModel path. A runtime resolver may map exact project/revision links to a safe local previewable OBJ/PLY/etc artifact and verify its digest before loading. Do not add a second rendering engine or treat a thumbnail as 3D authority.

Canonical library data must not store absolute project roots. When linked project/artifact bytes are unavailable, show an explicit unavailable/stale state while preserving metadata. Preview is read-only and must not mutate linked project geometry.

## Handoff

Publish implementation/evidence commit(s), then publish `coordination/sessions/M15-C001/PL-0342_CODEX_LOG_V01.md` separately. Record changed files, validation, limitations and final parity.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
