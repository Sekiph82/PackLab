# PL-0346 - Codex Prompt V01

Task: **Thumbnail and supplier contact-sheet export**
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

Implement local thumbnail/contact-sheet export for supplier discussions using PySide6 QImage/QPainter and accepted library metadata/preview sources.

Produce deterministic per-asset thumbnail records and a contact-sheet PNG for selected/all assets. Each tile must show at minimum asset ID/name plus concise supplier, nominal volume, material and closure metadata, with a visible provenance cue when a displayed value is PackLab-estimated rather than supplier factual.

Use accepted local thumbnail if digest-valid; otherwise generate from the existing QtRasterViewportAdapter when a resolvable 3D preview is available; otherwise use a deterministic placeholder. Do not use remote images.

Export to a user-selected destination only. Canonical export manifest records relative/logical tile identities, image SHA-256/dimensions and selected asset revision IDs, not the ambient absolute destination path. No supplier document attachment bytes are embedded.

## Handoff

Publish implementation/evidence commit(s), then publish `coordination/sessions/M15-C001/PL-0346_CODEX_LOG_V01.md` separately. Record changed files, validation, limitations and final parity.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
