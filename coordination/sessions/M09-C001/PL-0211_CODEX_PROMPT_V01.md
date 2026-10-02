# PL-0211 - Codex Work Order V01

Task: **Implement two-point distance measurement with snapping**

Repository: https://github.com/Sekiph82/PackLab
Cycle: M09-C001
Branch: `main`

Master prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/MASTER_CODEX_PROMPT_V01.md

Criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0211_CHATGPT_AUDIT_CRITERIA_V01.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0211_CODEX_LOG_V01.md

## Authorization and synchronization

Before material work, live `TASKS.md` must authorize M09-C001 / ordered PL-0202 through PL-0224 batch / READY / CODEX. Re-read the master prompt, repository rules, accepted M08 milestone audit and this child criteria. Safely fetch/fast-forward only when clean and behind-only. Never reset, clean, rebase, force-push or overwrite unrelated owner work.

Mandatory pre-reads:
- https://github.com/Sekiph82/PackLab/blob/main/docs/implementation/PL-0209_METRIC_SCALE_PROVENANCE.md

## Frozen scope

Implement a versioned two-point measurement service on normalized captured geometry with deterministic optional snapping to captured points/features. Record requested and snapped points, snap policy/radius, parent geometry/scale revision and units. Reject invalid coordinates, ambiguous snaps and stale geometry. Never claim better accuracy than scale provenance supports.

Preserve RAW_CAPTURE and accepted M08 artifacts. M09 may establish measurement/calibration evidence but must never fabricate physical evidence, owner measurements, printer verification or METRIC_VERIFIED state. AI_VISUAL_REFERENCE remains non-authoritative.

## Required tests/evidence

At minimum cover: exact distance, snap/no-snap boundary, ambiguous candidate, relative/metric units, invalid coordinates, deterministic provenance.

Run focused and predecessor regressions, the exact locked full pytest suite, changed-file Ruff/format, targeted mypy, compileall, `git diff --check`, protected-file/scope, dependency/license/privacy/secrets/generated/binary and remote-visibility checks. Use public/synthetic evidence unless the child explicitly requires owner-controlled physical evidence.

Use a separate implementation/evidence commit followed by a separate child-log-only commit. The log records exact commands/results, changed files, provenance/authority decisions and limitations, and ends exactly:

`READY_FOR_INDEPENDENT_AUDIT`

If all frozen gates are green and no real stop condition exists, continue directly to PL-0212 under the master batch without waiting for an intermediate ChatGPT audit. Stop only on FAILED/BLOCKED/OWNER_REQUIRED or a master stop condition.
