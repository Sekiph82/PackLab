# PL-0106 — Codex Work Order V01

Task: **PL-0106 — Lower/middle/upper capture rings for standard bottle mode**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/MASTER_CODEX_PROMPT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0106_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0106_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0106_CODEX_LOG_V01.md

## Authorization

TASKS.md must authorize `M04-BATCH-001` / `READY` / `CODEX`. M03 remains accepted. PL-0068 remains unchecked / OWNER_REQUIRED. Never edit TASKS.md or ChatGPT audits. Never start M05.

Reuse the M03 camera, AR/motion, quality, storage and diagnostics architecture. Coverage and auto-capture must consume authoritative accepted-capture/pose state and must not create a second sensor or still-capture owner.

## Mandatory implementation

1. Define standard-bottle orbit requirements for lower, middle and upper rings using the PL-0102 coverage model.
2. Make required sectors/ring counts explicit and configurable rather than hidden in UI code.
3. Completion must require all mandatory ring coverage, not just total frame count.
4. Expose missing-ring guidance to the UI and logging pipeline.
5. Add tests for each ring incomplete/complete, uneven coverage and boundary-sector assignment.

## Validation

Add deterministic behavior tests for normal, unavailable, failure and exact-boundary conditions. Run relevant regression/project/static checks, `git diff --check`, protected-file checks and privacy/signing review. Do not claim physical iPhone validation unless actually performed.

Create a distinct implementation commit, then a separate log-only commit. User-facing repository links must be full GitHub URLs.

End the log exactly:

`READY_FOR_INDEPENDENT_AUDIT`
