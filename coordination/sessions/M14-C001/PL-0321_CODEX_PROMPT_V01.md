# PL-0321 - Codex Prompt V01

Task: **Create starter materials: natural HDPE, white HDPE, clear PET, colored PET, PP cap**
Milestone: **M14 - Labels, Materials & Rendering**
Cycle: **M14-C001**

## M14 non-negotiable authority rules

- Read live root TASKS.md, M13 final audit, M09 physical-validation deferral, ADR-0005, and the exact predecessor child prompt/criteria before implementation.
- Design Model/CAD source revisions and stable semantic component/feature IDs remain authority. Tessellation/pixels are never promoted to geometric authority.
- RELATIVE/reconstruction_units never silently becomes millimetres.
- mm_unverified may carry numerical millimetres only with explicit UNVERIFIED physical status; no print-fit, mold, manufacturing, regulatory, material-certification, or production-readiness claim is allowed.
- Material/PBR/PCR data in M14 is visual/design metadata only unless a separately accepted certification authority exists; do not infer certified resin, recycled content, barrier, food-contact, mechanical, optical, or regulatory properties.
- Do not mutate or replace accepted M13 source authority.
- No runtime network download, private evidence, secrets, ambient absolute path leakage, or unreviewed dependency.
- Root TASKS.md lifecycle is ChatGPT-owned; Codex must not edit it.
- Each child gets an implementation/evidence commit and a distinct log-only commit ending exactly READY_FOR_INDEPENDENT_AUDIT.
- M15+ is unauthorized.

## Required implementation

Create a deterministic starter visual-material catalog using the accepted material/PBR schema for natural HDPE, white HDPE, clear PET, colored PET and PP cap. Values are curated render defaults only, not measured or certified specifications.

## Required validation

Cover at minimum: five required entries; unique stable IDs; correct family classification; valid PBR ranges; deterministic catalog bytes/model; visual-reference provenance; no certification or physical-performance claims.

Run focused predecessor/regression tests, the locked full repository suite, changed-file Ruff/format, targeted mypy/compile checks where applicable, dependency/lockfile check, scope/privacy/security review, and remote publication verification. Stop on any real failure or authority ambiguity.

## Handoff

Publish the implementation/evidence commit, then publish `coordination/sessions/M14-C001/PL-0321_CODEX_LOG_V01.md` in a separate log-only commit. Record exact changed files, commands/results, limitations, final local/origin/GitHub parity, and stop at this child if any mandatory criterion cannot be proved.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
