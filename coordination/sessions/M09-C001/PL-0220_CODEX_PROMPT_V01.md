# PL-0220 - Codex Work Order V01

Task: **Measure dimension error on matte bottle, glossy bottle and jerrycan**

Repository: https://github.com/Sekiph82/PackLab
Cycle: M09-C001
Branch: `main`

Master prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/MASTER_CODEX_PROMPT_V01.md

Criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0220_CHATGPT_AUDIT_CRITERIA_V01.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0220_CODEX_LOG_V01.md

## Authorization and synchronization

Before material work, live `TASKS.md` must authorize M09-C001 / ordered PL-0202 through PL-0224 batch / READY / CODEX. Re-read the master prompt, repository rules, accepted M08 milestone audit and this child criteria. Safely fetch/fast-forward only when clean and behind-only. Never reset, clean, rebase, force-push or overwrite unrelated owner work.

Mandatory pre-reads:
- https://github.com/Sekiph82/PackLab/blob/main/docs/calibration/benchmarks/first-physical-benchmark.md
- https://github.com/Sekiph82/PackLab/blob/main/docs/calibration/pre-use-verification.md
- https://github.com/Sekiph82/PackLab/blob/main/docs/implementation/PL-0209_METRIC_SCALE_PROVENANCE.md

## Frozen scope

Execute the M09 physical accuracy benchmark using owner-controlled caliper ground truth and corresponding authorized PackLab scan/measurement evidence for at least matte bottle, glossy bottle and jerrycan. Compute per-dimension signed/absolute/relative errors and aggregate statistics with complete provenance. Synthetic or nominal dimensions are not substitutes for physical ground truth.

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

At minimum cover: all three required object classes, ground-truth binding, per-dimension error math, missing/rejected sample accounting, deterministic aggregates, no nominal/synthetic substitution.

Run focused and predecessor regressions, the exact locked full pytest suite, changed-file Ruff/format, targeted mypy, compileall, `git diff --check`, protected-file/scope, dependency/license/privacy/secrets/generated/binary and remote-visibility checks. Use public/synthetic evidence unless this child explicitly requires owner-controlled physical evidence.

For a completed child, use a separate implementation/evidence commit followed by a separate child-log-only commit. A completed child log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

If all frozen gates are green and no real stop condition exists, continue directly to PL-0221 under the master batch without waiting for an intermediate ChatGPT audit.

Stop only on FAILED/BLOCKED/OWNER_REQUIRED or a master stop condition. M10 is unauthorized.
