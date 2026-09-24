# PL-0104 — Codex Work Order V01

Task: **PL-0104 — Automatic still capture from pose/overlap/quality thresholds**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/MASTER_CODEX_PROMPT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0104_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0104_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0104_CODEX_LOG_V01.md

## Authorization

TASKS.md must authorize `M04-BATCH-001` / `READY` / `CODEX`. M03 remains accepted. PL-0068 remains unchecked / OWNER_REQUIRED. Never edit TASKS.md or ChatGPT audits. Never start M05.

Reuse the M03 camera, AR/motion, quality, storage and diagnostics architecture. Coverage and auto-capture must consume authoritative accepted-capture/pose state and must not create a second sensor or still-capture owner.

## Mandatory implementation

1. Implement an auto-capture coordinator that requests a still only when pose eligibility, coverage target, overlap/parallax policy and PL-0100 quality gates are satisfied.
2. Use the existing health-gated production still-capture service and one camera/session owner; do not call NextLevel directly from a new path.
3. Prevent duplicate/in-flight auto-capture requests and define cooldown/rearm behavior after accepted or rejected candidates.
4. Manual capture must remain possible according to PL-0110 without corrupting auto-capture state.
5. Add deterministic tests for each gating reason, exact thresholds, overlap, cooldown, duplicate requests and recovery.

## Validation

Add deterministic behavior tests for normal, unavailable, failure and exact-boundary conditions. Run relevant regression/project/static checks, `git diff --check`, protected-file checks and privacy/signing review. Do not claim physical iPhone validation unless actually performed.

Create a distinct implementation commit, then a separate log-only commit. User-facing repository links must be full GitHub URLs.

End the log exactly:

`READY_FOR_INDEPENDENT_AUDIT`
