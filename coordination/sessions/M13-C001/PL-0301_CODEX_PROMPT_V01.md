# PL-0301 - Codex Work Order V01

Task: **Add STEP round-trip validation and bounding-dimension recheck**

Repository: https://github.com/Sekiph82/PackLab
Cycle: M13-C001
Branch: `main`

Master prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/MASTER_CODEX_PROMPT_V01.md

Criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0301_CHATGPT_AUDIT_CRITERIA_V01.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0301_CODEX_LOG_V01.md

## Authorization and synchronization

Live `TASKS.md` must authorize M13-C001 / PL-0289 through PL-0309 / READY / CODEX. Re-read M13 master, M12 AUDITED_PASS, ADR-0005, M09 physical deferral and this criteria. Synchronize safely; preserve owner work; no reset/clean/rebase/force-push.

Mandatory pre-reads:
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0297_CODEX_PROMPT_V01.md
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0300_CODEX_PROMPT_V01.md

## Frozen scope

Implement deterministic round-trip validation for exported STEP: reopen the exact exported file using the selected CAD adapter, verify readable solid/assembly topology, unit metadata, expected part count/names where supported, and recompute bounding dimensions in the exported coordinate system. Compare round-trip bounds against the pre-export CAD representation using an explicit numerical tolerance derived from serialization/kernel precision, not a physical manufacturing tolerance. Fail closed on unreadable STEP, unit mismatch, missing solids or excessive numerical drift. Preserve the distinction between numerical round-trip fidelity and real-world accuracy.

## Export authority rules

- Export artifacts are derived from exact source revisions and never replace Scan Master, Design Model or CAD/BREP truth.
- `mm_unverified` may be encoded numerically as millimetres only when explicitly permitted by the child contract and must remain physically unverified.
- `RELATIVE` / `reconstruction_units` must never silently become millimetres.
- Successful export/round-trip is numerical/software evidence, not physical/mold/manufacturing validation.
- PL-0220 through PL-0224 remain DEFERRED_OWNER_VALIDATION.
- M14+ implementation is unauthorized.

## Required tests/evidence

At minimum cover: known simple revolve/loft round-trip; unit=mm check; bounds within explicit numerical tolerance; corrupted STEP; missing solid; part/name checks where supported; deterministic report; numerical fidelity != physical tolerance.

Run focused/predecessor regressions, exact locked full pytest, changed-file Ruff/format, targeted mypy, compileall, diff/scope/dependency/license/privacy/secrets/generated/binary/remote checks.

Use separate implementation/evidence and child-log-only commits. Completed log ends exactly `READY_FOR_INDEPENDENT_AUDIT`. If green continue directly to PL-0302; stop only on real FAILED/BLOCKED/OWNER_REQUIRED/master stop.
