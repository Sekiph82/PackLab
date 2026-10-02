# PL-0221 - Codex Work Order V01

Task: **Establish V1 measurement acceptance thresholds from benchmark evidence**

Repository: https://github.com/Sekiph82/PackLab
Cycle: M09-C001
Branch: `main`

Master prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/MASTER_CODEX_PROMPT_V01.md

Criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0221_CHATGPT_AUDIT_CRITERIA_V01.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0221_CODEX_LOG_V01.md

## Authorization and synchronization

Before material work, live `TASKS.md` must authorize M09-C001 / ordered PL-0202 through PL-0224 batch / READY / CODEX. Re-read the master prompt, repository rules, accepted M08 milestone audit and this child criteria. Safely fetch/fast-forward only when clean and behind-only. Never reset, clean, rebase, force-push or overwrite unrelated owner work.

Mandatory pre-reads:
- https://github.com/Sekiph82/PackLab/blob/main/docs/calibration/benchmarks/first-physical-benchmark.md

## Frozen scope

Derive and document V1 acceptance thresholds for overall dimensions and key features only from the accepted PL-0220 physical benchmark evidence. Publish the dataset/revision used, statistical rule, inclusivity, sample limitations and failure policy. Do not invent thresholds if physical evidence is insufficient or unrepresentative.

Preserve RAW_CAPTURE and accepted M08 artifacts. AI_VISUAL_REFERENCE remains non-authoritative. Measurement/metric claims must remain inside the exact M09 scale/provenance state machine.

## Evidence dependency gate

This child depends on accepted evidence from earlier M09 physical benchmark children. If the required predecessor physical evidence is missing or the batch previously stopped at OWNER_REQUIRED, this child is not authorized to synthesize substitutes or continue independently.

## Required tests/evidence

At minimum cover: threshold derivation reproducibility, inclusive boundaries, insufficient-evidence rejection, dataset revision binding, no cherry-picking, limitation statement.

Run focused and predecessor regressions, the exact locked full pytest suite, changed-file Ruff/format, targeted mypy, compileall, `git diff --check`, protected-file/scope, dependency/license/privacy/secrets/generated/binary and remote-visibility checks. Use public/synthetic evidence unless this child explicitly requires owner-controlled physical evidence.

For a completed child, use a separate implementation/evidence commit followed by a separate child-log-only commit. A completed child log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

If all frozen gates are green and no real stop condition exists, continue directly to PL-0222 under the master batch without waiting for an intermediate ChatGPT audit.

Stop only on FAILED/BLOCKED/OWNER_REQUIRED or a master stop condition. M10 is unauthorized.
