# PL-0266 - Codex Work Order V01

Task: **Add closure dimensions to measurement report**

Repository: https://github.com/Sekiph82/PackLab
Cycle: M11-C001
Branch: `main`

Master prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/MASTER_CODEX_PROMPT_V01.md

Criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0266_CHATGPT_AUDIT_CRITERIA_V01.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0266_CODEX_LOG_V01.md

## Authorization and synchronization

Live `TASKS.md` must authorize M11-C001 / PL-0241 through PL-0267 batch / READY / CODEX. Re-read the M11 master, M10 audit, M09 deferral, repository rules and this criteria. Synchronize safely; never reset/clean/rebase/force-push over owner work.

Mandatory pre-reads:
- https://github.com/Sekiph82/PackLab/blob/main/core/src/packlab_core/measurement_report.py
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/M09_PHYSICAL_VALIDATION_DEFERRAL_OWNER_DECISION_V01.md

## Frozen scope

Extend the existing measurement/report layer with Design Model closure dimensions that are explicitly sourced from the parametric closure revision and exact Scan Master/scale parent. Keep captured measurements distinct from modeled dimensions. Use inherited units and uncertainty/fit evidence; while physical validation is deferred, never label closure dimensions certified/mold-ready.

## Authority rules

Exact Scan Master parent remains immutable. Design Model/assembly revisions are separate parametric truth. `METRIC_UNVERIFIED` stays unverified and physical/mold/manufacturing claims remain prohibited while PL-0220–0224 are deferred. No M12+ advanced geometry or M13 CAD/BREP implementation.

## Required tests/evidence

At minimum cover: cylindrical/flip-top dimension summaries, parametric-vs-captured source labeling, parent/scale binding, stale model rejection, mm_unverified semantics, deterministic report, no certified claim.

Run focused/predecessor regressions, exact locked full pytest, changed-file Ruff/format, targeted mypy, compileall, `git diff --check`, protected scope, dependency/license/privacy/secrets/generated/binary and remote checks.

Use separate implementation/evidence and child-log-only commits. Completed log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

If green, continue directly to PL-0267 under the M11 master batch without waiting for intermediate ChatGPT audit.

Stop only on real FAILED/BLOCKED/OWNER_REQUIRED/master stop.
