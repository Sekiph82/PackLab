# PL-0110 — Codex Work Order V01

Task: **PL-0110 — Manual-capture override with quality warnings**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/MASTER_CODEX_PROMPT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0110_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0110_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0110_CODEX_LOG_V01.md

## Authorization

TASKS.md must authorize `M04-BATCH-001` / `READY` / `CODEX`. M03 remains accepted. PL-0068 remains unchecked / OWNER_REQUIRED. Never edit TASKS.md or ChatGPT audits. Never start M05.

Reuse the M03 camera, AR/motion, quality, storage and diagnostics architecture. Coverage and auto-capture must consume authoritative accepted-capture/pose state and must not create a second sensor or still-capture owner.

## Mandatory implementation

1. Add a manual capture action that can request a still even when auto-capture conditions are not met, while preserving hard safety/admission gates.
2. Show and persist quality warnings/reasons when the user manually accepts a candidate that would not auto-capture.
3. Define which conditions are never overridable, such as health hard-stop, camera/session failure or unusable source capture.
4. Manual override must not bypass immutable-source, metadata, pose/motion or session transaction rules.
5. Add tests for warning override, non-overridable failures, accepted manual capture logging and interaction with auto-capture cooldown/state.

## Validation

Add deterministic behavior tests for normal, unavailable, failure and exact-boundary conditions. Run relevant regression/project/static checks, `git diff --check`, protected-file checks and privacy/signing review. Do not claim physical iPhone validation unless actually performed.

Create a distinct implementation commit, then a separate log-only commit. User-facing repository links must be full GitHub URLs.

End the log exactly:

`READY_FOR_INDEPENDENT_AUDIT`
