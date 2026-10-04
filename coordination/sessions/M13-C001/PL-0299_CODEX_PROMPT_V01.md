# PL-0299 - Codex Work Order V01

Task: **Export OBJ and GLB from Design Model with stable part naming**

Repository: https://github.com/Sekiph82/PackLab
Cycle: M13-C001
Branch: `main`

Master prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/MASTER_CODEX_PROMPT_V01.md

Criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0299_CHATGPT_AUDIT_CRITERIA_V01.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0299_CODEX_LOG_V01.md

## Authorization and synchronization

Live `TASKS.md` must authorize M13-C001 / PL-0289 through PL-0309 / READY / CODEX. Re-read M13 master, M12 AUDITED_PASS, ADR-0005, M09 physical deferral and this criteria. Synchronize safely; preserve owner work; no reset/clean/rebase/force-push.

Mandatory pre-reads:
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0296_CODEX_PROMPT_V01.md
- https://github.com/Sekiph82/PackLab/blob/main/core/src/packlab_core/assembly_hierarchy_export.py

## Frozen scope

Implement deterministic OBJ and GLB export from M13 tessellated Design Model/assembly geometry with stable semantic part/component names and provenance. OBJ may remain in source model units with manifest-declared unit semantics. GLB may apply a documented coordinate-unit conversion required by the format/viewer, but that transform must be explicit, reversible in metadata and must not upgrade authority. Preserve component hierarchy where practical, stable names, material-free geometry identity, parent-authority mode and exact Design Model/CAD revisions. Do not use these exports as Scan Master or CAD/BREP truth.

## Export authority rules

- Export artifacts are derived from exact source revisions and never replace Scan Master, Design Model or CAD/BREP truth.
- `mm_unverified` may be encoded numerically as millimetres only when explicitly permitted by the child contract and must remain physically unverified.
- `RELATIVE` / `reconstruction_units` must never silently become millimetres.
- Successful export/round-trip is numerical/software evidence, not physical/mold/manufacturing validation.
- PL-0220 through PL-0224 remain DEFERRED_OWNER_VALIDATION.
- M14+ implementation is unauthorized.

## Required tests/evidence

At minimum cover: single/multipart OBJ; GLB nodes/part names; deterministic geometry; explicit unit transform metadata; RELATIVE and mm_unverified handling; assembly hierarchy where supported; round-trip/basic parse; derived-export authority only.

Run focused/predecessor regressions, exact locked full pytest, changed-file Ruff/format, targeted mypy, compileall, diff/scope/dependency/license/privacy/secrets/generated/binary/remote checks.

Use separate implementation/evidence and child-log-only commits. Completed log ends exactly `READY_FOR_INDEPENDENT_AUDIT`. If green continue directly to PL-0300; stop only on real FAILED/BLOCKED/OWNER_REQUIRED/master stop.
