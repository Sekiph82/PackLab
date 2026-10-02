# PL-0224 - Codex Work Order V01

Task: **Document measurement-use limits for mold manufacturing**

Repository: https://github.com/Sekiph82/PackLab
Cycle: M09-C001
Branch: `main`

Master prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/MASTER_CODEX_PROMPT_V01.md

Criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0224_CHATGPT_AUDIT_CRITERIA_V01.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0224_CODEX_LOG_V01.md

## Authorization and synchronization

Before material work, live `TASKS.md` must authorize M09-C001 / ordered PL-0202 through PL-0224 batch / READY / CODEX. Re-read the master prompt, repository rules, accepted M08 milestone audit and this child criteria. Safely fetch/fast-forward only when clean and behind-only. Never reset, clean, rebase, force-push or overwrite unrelated owner work.

Mandatory pre-reads:
- https://github.com/Sekiph82/PackLab/blob/main/docs/implementation/PL-0209_METRIC_SCALE_PROVENANCE.md
- https://github.com/Sekiph82/PackLab/blob/main/docs/calibration/benchmarks/first-physical-benchmark.md

## Frozen scope

Produce the final M09 measurement safety/usage document grounded in the accepted M09 contracts and physical benchmark evidence. State exactly when PackLab measurements are diagnostic, estimate-only, METRIC_UNVERIFIED or METRIC_VERIFIED, what benchmark/uncertainty thresholds apply, and conditions under which measurements must not be used for mold manufacturing. Do not broaden authority beyond evidence.

Preserve RAW_CAPTURE and accepted M08 artifacts. AI_VISUAL_REFERENCE remains non-authoritative. Measurement/metric claims must remain inside the exact M09 scale/provenance state machine.

## Evidence dependency gate

This child depends on accepted evidence from earlier M09 physical benchmark children. If the required predecessor physical evidence is missing or the batch previously stopped at OWNER_REQUIRED, this child is not authorized to synthesize substitutes or continue independently.

## Required tests/evidence

At minimum cover: document links actual accepted benchmark/threshold revisions, distinguishes all scale states, includes no-mold conditions and uncertainty limits, no unsupported certification claim.

Run focused and predecessor regressions, the exact locked full pytest suite, changed-file Ruff/format, targeted mypy, compileall, `git diff --check`, protected-file/scope, dependency/license/privacy/secrets/generated/binary and remote-visibility checks. Use public/synthetic evidence unless this child explicitly requires owner-controlled physical evidence.

For a completed child, use a separate implementation/evidence commit followed by a separate child-log-only commit. A completed child log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

If this final child is validation-green, complete and publish the M09 master log with `BATCH_COMPLETED` and terminal `AWAITING_MILESTONE_AUDIT`, verify remote parity, then stop. Do not start M10.

Stop only on FAILED/BLOCKED/OWNER_REQUIRED or a master stop condition. M10 is unauthorized.
