# PL-0297 - Codex Work Order V01

Task: **Export Design Model/assembly to STEP with explicit millimetre units**

Repository: https://github.com/Sekiph82/PackLab
Cycle: M13-C001
Branch: `main`

Master prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/MASTER_CODEX_PROMPT_V01.md

Criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0297_CHATGPT_AUDIT_CRITERIA_V01.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0297_CODEX_LOG_V01.md

## Authorization and synchronization

Live `TASKS.md` must authorize M13-C001 / PL-0289 through PL-0309 / READY / CODEX. Re-read M13 master, M12 AUDITED_PASS, ADR-0005, M09 physical deferral and this criteria. Synchronize safely; preserve owner work; no reset/clean/rebase/force-push.

Mandatory pre-reads:
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0294_CODEX_PROMPT_V01.md
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0295_CODEX_PROMPT_V01.md
- https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/adr/ADR-0005-standalone-design-geometry-root.md

## Frozen scope

Implement deterministic STEP export from a validated M13 CAD/BREP representation for one Design Model or supported assembly. STEP export is permitted only when the source coordinate unit is `mm_unverified`; RELATIVE/reconstruction_units must fail closed rather than silently scaling to millimetres. Write STEP units as millimetres and preserve part/assembly names and stable feature/component labels where the selected binding supports them. Export metadata must state that millimetre units are numerically encoded but physical accuracy remains unverified and mold/manufacturing suitability is not authorized. Preserve exact Design Model revision, CAD representation revision, parent-authority mode and selected CAD/kernel version.

## Export authority rules

- Export artifacts are derived from exact source revisions and never replace Scan Master, Design Model or CAD/BREP truth.
- `mm_unverified` may be encoded numerically as millimetres only when explicitly permitted by the child contract and must remain physically unverified.
- `RELATIVE` / `reconstruction_units` must never silently become millimetres.
- Successful export/round-trip is numerical/software evidence, not physical/mold/manufacturing validation.
- PL-0220 through PL-0224 remain DEFERRED_OWNER_VALIDATION.
- M14+ implementation is unauthorized.

## Required tests/evidence

At minimum cover: single-part STEP; assembly STEP if supported by selected binding; mm_unverified source accepted; RELATIVE source rejected; deterministic file/manifest identity; part names; stable feature mapping where available; reopened unit check; no physical/mold claim.

Run focused/predecessor regressions, exact locked full pytest, changed-file Ruff/format, targeted mypy, compileall, diff/scope/dependency/license/privacy/secrets/generated/binary/remote checks.

Use separate implementation/evidence and child-log-only commits. Completed log ends exactly `READY_FOR_INDEPENDENT_AUDIT`. If green continue directly to PL-0298; stop only on real FAILED/BLOCKED/OWNER_REQUIRED/master stop.
