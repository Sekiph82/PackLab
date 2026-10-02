# PL-0214 - Codex Work Order V01

Task: **Extract vertical profiles and silhouettes**

Repository: https://github.com/Sekiph82/PackLab
Cycle: M09-C001
Branch: `main`

Master prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/MASTER_CODEX_PROMPT_V01.md

Criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0214_CHATGPT_AUDIT_CRITERIA_V01.md

Required log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0214_CODEX_LOG_V01.md

## Authorization and synchronization

Before material work, live `TASKS.md` must authorize M09-C001 / ordered PL-0202 through PL-0224 batch / READY / CODEX. Re-read the master prompt, repository rules, accepted M08 milestone audit and this child criteria. Safely fetch/fast-forward only when clean and behind-only. Never reset, clean, rebase, force-push or overwrite unrelated owner work.

Mandatory pre-reads:
- https://github.com/Sekiph82/PackLab/blob/main/docs/implementation/PL-0209_METRIC_SCALE_PROVENANCE.md

## Frozen scope

Implement deterministic vertical profile/silhouette extraction in an explicitly selected canonical vertical plane/direction from normalized captured geometry. Record plane/direction, sampling/tolerance policy, parent revision and scale state. Reject degenerate planes and insufficient evidence; do not smooth away captured features or fabricate missing outline.

Preserve RAW_CAPTURE and accepted M08 artifacts. AI_VISUAL_REFERENCE remains non-authoritative. Measurement/metric claims must remain inside the exact M09 scale/provenance state machine.

## Required tests/evidence

At minimum cover: front/side synthetic profiles, arbitrary valid plane, degenerate direction, sparse/empty evidence, deterministic ordering, relative/metric units, source immutability.

Run focused and predecessor regressions, the exact locked full pytest suite, changed-file Ruff/format, targeted mypy, compileall, `git diff --check`, protected-file/scope, dependency/license/privacy/secrets/generated/binary and remote-visibility checks. Use public/synthetic evidence unless this child explicitly requires owner-controlled physical evidence.

For a completed child, use a separate implementation/evidence commit followed by a separate child-log-only commit. A completed child log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

If all frozen gates are green and no real stop condition exists, continue directly to PL-0215 under the master batch without waiting for an intermediate ChatGPT audit.

Stop only on FAILED/BLOCKED/OWNER_REQUIRED or a master stop condition. M10 is unauthorized.
