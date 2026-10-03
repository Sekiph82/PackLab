# PL-0261 - Codex Work Order V01

Task: **Separate cap/closure from body when scan evidence allows**

Repository: https://github.com/Sekiph82/PackLab
Cycle: M11-C001
Branch: `main`

Master prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/MASTER_CODEX_PROMPT_V01.md

Criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0261_CHATGPT_AUDIT_CRITERIA_V01.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0261_CODEX_LOG_V01.md

## Authorization and synchronization

Live `TASKS.md` must authorize M11-C001 / PL-0241 through PL-0267 batch / READY / CODEX. Re-read the M11 master, M10 audit, M09 deferral, repository rules and this criteria. Synchronize safely; never reset/clean/rebase/force-push over owner work.

Mandatory pre-reads:
- https://github.com/Sekiph82/PackLab/blob/main/core/src/packlab_core/neck_finish_candidates.py
- https://github.com/Sekiph82/PackLab/blob/main/core/src/packlab_core/scan_master.py

## Frozen scope

Implement deterministic evidence-driven cap/closure separation candidates from the selected Scan Master and accepted neck/finish/profile evidence. Separation must be conservative, preserve captured parent geometry, expose ambiguity/support evidence and create Design Model component candidates only when evidence is sufficient. Do not destructively split Scan Master or invent hidden closure geometry.

## Authority rules

Exact Scan Master parent remains immutable. Design Model/assembly revisions are separate parametric truth. `METRIC_UNVERIFIED` stays unverified and physical/mold/manufacturing claims remain prohibited while PL-0220–0224 are deferred. No M12+ advanced geometry or M13 CAD/BREP implementation.

## Required tests/evidence

At minimum cover: clear cap/body separation, ambiguous/no-separation case, support thresholds, stale parent, stable feature/component IDs, no Scan Master mutation, unit/deferred status.

Run focused/predecessor regressions, exact locked full pytest, changed-file Ruff/format, targeted mypy, compileall, `git diff --check`, protected scope, dependency/license/privacy/secrets/generated/binary and remote checks.

Use separate implementation/evidence and child-log-only commits. Completed log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

If green, continue directly to PL-0262 under the M11 master batch without waiting for intermediate ChatGPT audit.

Stop only on real FAILED/BLOCKED/OWNER_REQUIRED/master stop.
