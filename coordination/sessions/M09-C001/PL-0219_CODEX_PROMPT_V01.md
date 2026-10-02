# PL-0219 - Codex Work Order V01

Task: **Define the physical accuracy benchmark set and record contract**

Repository: https://github.com/Sekiph82/PackLab
Cycle: M09-C001
Branch: `main`

Master prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/MASTER_CODEX_PROMPT_V01.md

Criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0219_CHATGPT_AUDIT_CRITERIA_V01.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0219_CODEX_LOG_V01.md

## Authorization and synchronization

Before material work, live `TASKS.md` must authorize M09-C001 / ordered PL-0202 through PL-0224 batch / READY / CODEX. Re-read the master prompt, repository rules, accepted M08 milestone audit and this child criteria. Safely fetch/fast-forward only when clean and behind-only. Never reset, clean, rebase, force-push or overwrite unrelated owner work.

Mandatory pre-reads:
- https://github.com/Sekiph82/PackLab/blob/main/docs/calibration/benchmarks/first-physical-benchmark.md
- https://github.com/Sekiph82/PackLab/blob/main/docs/calibration/benchmarks/benchmark-record-template.md
- https://github.com/Sekiph82/PackLab/blob/main/docs/calibration/pre-use-verification.md

## Frozen scope

Define the versioned owner-executed physical benchmark protocol, safe record schema/template and evidence requirements for at least matte bottle, glossy bottle and jerrycan. Specify caliper ground-truth fields, stable sample IDs, scan/measurement revision links, environmental/setup metadata, missing/rejected dispositions and privacy boundary. This child defines the benchmark package only and must not invent measured values or acceptance thresholds.

Preserve RAW_CAPTURE and accepted M08 artifacts. AI_VISUAL_REFERENCE remains non-authoritative. Measurement/metric claims must remain inside the exact M09 scale/provenance state machine.

## Required tests/evidence

At minimum cover: schema/template validation, missing ground truth, rejected sample retention, privacy-safe references, deterministic record identity, no fabricated measurements/thresholds.

Run focused and predecessor regressions, the exact locked full pytest suite, changed-file Ruff/format, targeted mypy, compileall, `git diff --check`, protected-file/scope, dependency/license/privacy/secrets/generated/binary and remote-visibility checks. Use public/synthetic evidence unless this child explicitly requires owner-controlled physical evidence.

For a completed child, use a separate implementation/evidence commit followed by a separate child-log-only commit. A completed child log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

If all frozen gates are green and no real stop condition exists, continue directly to PL-0220 under the master batch without waiting for an intermediate ChatGPT audit.

Stop only on FAILED/BLOCKED/OWNER_REQUIRED or a master stop condition. M10 is unauthorized.
