# PL-0267 - Codex Work Order V01

Task: **Validate bottle/cap assembly transforms on export**

Repository: https://github.com/Sekiph82/PackLab
Cycle: M11-C001
Branch: `main`

Master prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/MASTER_CODEX_PROMPT_V01.md

Criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0267_CHATGPT_AUDIT_CRITERIA_V01.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0267_CODEX_LOG_V01.md

## Authorization and synchronization

Live `TASKS.md` must authorize M11-C001 / PL-0241 through PL-0267 batch / READY / CODEX. Re-read the M11 master, M10 audit, M09 deferral, repository rules and this criteria. Synchronize safely; never reset/clean/rebase/force-push over owner work.

Mandatory pre-reads:
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0264_CODEX_PROMPT_V01.md
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0265_CODEX_PROMPT_V01.md

## Frozen scope

Implement deterministic validation/export metadata for bottle+closure Design Model assembly transforms. Check mating reference IDs/axes/planes, component revisions, transform rigidity and unit/scale consistency before export handoff. This child validates assembly transforms and produces export-ready metadata/preview relationships only; actual CAD/STEP export remains M13. Reject stale/incompatible components and preserve deferred physical-validation limits.

## Authority rules

Exact Scan Master parent remains immutable. Design Model/assembly revisions are separate parametric truth. `METRIC_UNVERIFIED` stays unverified and physical/mold/manufacturing claims remain prohibited while PL-0220–0224 are deferred. No M12+ advanced geometry or M13 CAD/BREP implementation.

## Required tests/evidence

At minimum cover: identity/known valid transform, stale component, non-rigid transform, axis/plane mismatch, unit mismatch, deterministic assembly metadata, mm_unverified/deferred disclaimer, no STEP/CAD implementation.

Run focused/predecessor regressions, exact locked full pytest, changed-file Ruff/format, targeted mypy, compileall, `git diff --check`, protected scope, dependency/license/privacy/secrets/generated/binary and remote checks.

Use separate implementation/evidence and child-log-only commits. Completed log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

If this final child is green, complete the M11 master log as BATCH_COMPLETED, verify clean local/origin/GitHub parity, confirm M12 was not started, end the master log exactly `AWAITING_MILESTONE_AUDIT`, publish it separately and stop.

Stop only on real FAILED/BLOCKED/OWNER_REQUIRED/master stop.
