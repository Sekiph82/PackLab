# PL-0205 - Codex Work Order V01

Task: **Detect object ground/base plane with user override**

Repository: https://github.com/Sekiph82/PackLab
Cycle: M09-C001
Branch: `main`

Master prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/MASTER_CODEX_PROMPT_V01.md

Criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0205_CHATGPT_AUDIT_CRITERIA_V01.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0205_CODEX_LOG_V01.md

## Authorization and synchronization

Before material work, live `TASKS.md` must authorize M09-C001 / ordered PL-0202 through PL-0224 batch / READY / CODEX. Re-read the master prompt, repository rules, accepted M08 milestone audit and this child criteria. Safely fetch/fast-forward only when clean and behind-only. Never reset, clean, rebase, force-push or overwrite unrelated owner work.

Mandatory pre-reads:
- https://github.com/Sekiph82/PackLab/blob/main/core/src/packlab_core/object_mask_lifting.py
- https://github.com/Sekiph82/PackLab/blob/main/docs/implementation/PL-0209_METRIC_SCALE_PROVENANCE.md

## Frozen scope

Implement deterministic base/ground-plane candidate detection from captured object geometry using a bounded robust policy, with evidence/confidence and an explicit manual override contract. Automatic results are candidates, not hidden truth. Overrides must be versioned/provenance-bound and never mutate source geometry. Do not perform upright/front selection beyond the plane normal needed by this child.

Preserve RAW_CAPTURE and accepted M08 artifacts. M09 may establish measurement/calibration evidence but must never fabricate physical evidence, owner measurements, printer verification or METRIC_VERIFIED state. AI_VISUAL_REFERENCE remains non-authoritative.

## Required tests/evidence

At minimum cover: flat synthetic base, noisy/outlier cloud, ambiguous/no-plane, threshold boundaries, override acceptance/rejection, parent revision invalidation, source immutability.

Run focused and predecessor regressions, the exact locked full pytest suite, changed-file Ruff/format, targeted mypy, compileall, `git diff --check`, protected-file/scope, dependency/license/privacy/secrets/generated/binary and remote-visibility checks. Use public/synthetic evidence unless the child explicitly requires owner-controlled physical evidence.

Use a separate implementation/evidence commit followed by a separate child-log-only commit. The log records exact commands/results, changed files, provenance/authority decisions and limitations, and ends exactly:

`READY_FOR_INDEPENDENT_AUDIT`

If all frozen gates are green and no real stop condition exists, continue directly to PL-0206 under the master batch without waiting for an intermediate ChatGPT audit. Stop only on FAILED/BLOCKED/OWNER_REQUIRED or a master stop condition.
