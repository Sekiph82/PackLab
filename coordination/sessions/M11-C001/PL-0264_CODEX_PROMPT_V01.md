# PL-0264 - Codex Work Order V01

Task: **Define neck/closure mating reference planes and axes**

Repository: https://github.com/Sekiph82/PackLab
Cycle: M11-C001
Branch: `main`

Master prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/MASTER_CODEX_PROMPT_V01.md

Criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0264_CHATGPT_AUDIT_CRITERIA_V01.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0264_CODEX_LOG_V01.md

## Authorization and synchronization

Live `TASKS.md` must authorize M11-C001 / PL-0241 through PL-0267 batch / READY / CODEX. Re-read the M11 master, M10 audit, M09 deferral, repository rules and this criteria. Synchronize safely; never reset/clean/rebase/force-push over owner work.

Mandatory pre-reads:
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0242_CODEX_PROMPT_V01.md
- https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0253_CODEX_PROMPT_V01.md

## Frozen scope

Define stable parametric mating reference entities between bottle neck/finish and closure: canonical axis, neck/closure reference planes and explicit offsets. Bind references to stable feature IDs and current Design Model revision. Validate coaxial/alignment assumptions and expose mismatches; do not claim sealing/thread compatibility.

## Authority rules

Exact Scan Master parent remains immutable. Design Model/assembly revisions are separate parametric truth. `METRIC_UNVERIFIED` stays unverified and physical/mold/manufacturing claims remain prohibited while PL-0220–0224 are deferred. No M12+ advanced geometry or M13 CAD/BREP implementation.

## Required tests/evidence

At minimum cover: coaxial reference creation, offset plane, stale feature rejection, non-coaxial mismatch, deterministic IDs, edit persistence, no compatibility/seal claim.

Run focused/predecessor regressions, exact locked full pytest, changed-file Ruff/format, targeted mypy, compileall, `git diff --check`, protected scope, dependency/license/privacy/secrets/generated/binary and remote checks.

Use separate implementation/evidence and child-log-only commits. Completed log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

If green, continue directly to PL-0265 under the M11 master batch without waiting for intermediate ChatGPT audit.

Stop only on real FAILED/BLOCKED/OWNER_REQUIRED/master stop.
