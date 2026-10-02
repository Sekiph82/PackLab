# PL-0209 - Codex Work Order V01

Task: **Persist scale provenance, uncertainty and scale-state promotion rules**

Repository: https://github.com/Sekiph82/PackLab
Cycle: M09-C001
Branch: `main`

Master prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/MASTER_CODEX_PROMPT_V01.md

Criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0209_CHATGPT_AUDIT_CRITERIA_V01.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0209_CODEX_LOG_V01.md

## Authorization and synchronization

Before material work, live `TASKS.md` must authorize M09-C001 / ordered PL-0202 through PL-0224 batch / READY / CODEX. Re-read the master prompt, repository rules, accepted M08 milestone audit and this child criteria. Safely fetch/fast-forward only when clean and behind-only. Never reset, clean, rebase, force-push or overwrite unrelated owner work.

Mandatory pre-reads:
- https://github.com/Sekiph82/PackLab/blob/main/docs/implementation/PL-0209_METRIC_SCALE_PROVENANCE.md
- https://github.com/Sekiph82/PackLab/blob/main/docs/calibration/pre-use-verification.md
- https://github.com/Sekiph82/PackLab/blob/main/docs/calibration/benchmarks/first-physical-benchmark.md

## Frozen scope

Implement the mandatory ScaleProvenance contract and explicit RELATIVE / METRIC_UNVERIFIED / METRIC_VERIFIED state machine. Promotion to METRIC_VERIFIED requires accepted owner-controlled physical scale evidence; nominal SVG values, synthetic fixtures, neural metric depth and unverified printer output cannot promote. Persist calibration observation IDs, physical reference and units, scale factor, residuals, rejected observations, algorithm version, parent reconstruction, uncertainty, timestamp and actor/process provenance. Parent changes invalidate derived scale.

Preserve RAW_CAPTURE and accepted M08 artifacts. M09 may establish measurement/calibration evidence but must never fabricate physical evidence, owner measurements, printer verification or METRIC_VERIFIED state. AI_VISUAL_REFERENCE remains non-authoritative.

## Required tests/evidence

At minimum cover: relative cannot claim mm, verified/unverified promotion rules, rejected evidence exclusion, parent invalidation, persistence/reopen, AI_VISUAL_REFERENCE isolation, deterministic factor application.

Run focused and predecessor regressions, the exact locked full pytest suite, changed-file Ruff/format, targeted mypy, compileall, `git diff --check`, protected-file/scope, dependency/license/privacy/secrets/generated/binary and remote-visibility checks. Use public/synthetic evidence unless the child explicitly requires owner-controlled physical evidence.

Use a separate implementation/evidence commit followed by a separate child-log-only commit. The log records exact commands/results, changed files, provenance/authority decisions and limitations, and ends exactly:

`READY_FOR_INDEPENDENT_AUDIT`

If all frozen gates are green and no real stop condition exists, continue directly to PL-0210 under the master batch without waiting for an intermediate ChatGPT audit. Stop only on FAILED/BLOCKED/OWNER_REQUIRED or a master stop condition.
