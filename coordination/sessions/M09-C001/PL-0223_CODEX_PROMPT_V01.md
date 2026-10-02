# PL-0223 - Codex Work Order V01

Task: **Run calibration-mat print-scale sensitivity benchmark**

Repository: https://github.com/Sekiph82/PackLab
Cycle: M09-C001
Branch: `main`

Master prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/MASTER_CODEX_PROMPT_V01.md

Criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0223_CHATGPT_AUDIT_CRITERIA_V01.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0223_CODEX_LOG_V01.md

## Authorization and synchronization

Before material work, live `TASKS.md` must authorize M09-C001 / ordered PL-0202 through PL-0224 batch / READY / CODEX. Re-read the master prompt, repository rules, accepted M08 milestone audit and this child criteria. Safely fetch/fast-forward only when clean and behind-only. Never reset, clean, rebase, force-push or overwrite unrelated owner work.

Mandatory pre-reads:
- https://github.com/Sekiph82/PackLab/blob/main/docs/calibration/pre-use-verification.md
- https://github.com/Sekiph82/PackLab/blob/main/docs/calibration/mat-assets.md
- https://github.com/Sekiph82/PackLab/blob/main/docs/calibration/benchmarks/first-physical-benchmark.md

## Frozen scope

Execute an owner-controlled physical print-scale sensitivity study using measured printed-mat geometry and multiple recorded print-scale conditions/attempts. Quantify how print scaling propagates into PackLab scale/measurement outputs. Retain rejected prints and settings. Nominal SVG geometry or synthetic scaling cannot satisfy this physical benchmark.

Preserve RAW_CAPTURE and accepted M08 artifacts. AI_VISUAL_REFERENCE remains non-authoritative. Measurement/metric claims must remain inside the exact M09 scale/provenance state machine.

## Mandatory owner-controlled physical evidence gate

This task **cannot** be completed from synthetic fixtures, nominal CAD/SVG dimensions, generated data or builder inference. Before claiming implementation completion, verify that the required owner-controlled physical measurements/scans/records are available through authorized project evidence.

If they are absent, incomplete, private-but-not-authorized for this run, or fail their pre-use verification:
1. do not fabricate values;
2. do not mark the child PASS;
3. publish a blocker child log recording the exact missing evidence;
4. set the master frontier to `OWNER_REQUIRED_PHYSICAL_BENCHMARK_EVIDENCE` and `BATCH_STOPPED`;
5. stop the M09 batch.

## Required tests/evidence

At minimum cover: accepted and deliberately varied/rejected print attempts, owner-measured geometry, scale-error propagation, provenance, deterministic analysis, no nominal-only PASS.

Run focused and predecessor regressions, the exact locked full pytest suite, changed-file Ruff/format, targeted mypy, compileall, `git diff --check`, protected-file/scope, dependency/license/privacy/secrets/generated/binary and remote-visibility checks. Use public/synthetic evidence unless this child explicitly requires owner-controlled physical evidence.

For a completed child, use a separate implementation/evidence commit followed by a separate child-log-only commit. A completed child log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

If all frozen gates are green and no real stop condition exists, continue directly to PL-0224 under the master batch without waiting for an intermediate ChatGPT audit.

Stop only on FAILED/BLOCKED/OWNER_REQUIRED or a master stop condition. M10 is unauthorized.
