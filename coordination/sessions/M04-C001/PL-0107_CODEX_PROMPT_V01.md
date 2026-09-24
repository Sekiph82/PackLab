# PL-0107 — Codex Work Order V01

Task: **PL-0107 — Top/neck detail pass**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/MASTER_CODEX_PROMPT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0107_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0107_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0107_CODEX_LOG_V01.md

## Authorization

TASKS.md must authorize `M04-BATCH-001` / `READY` / `CODEX`. M03 remains accepted. PL-0068 remains unchecked / OWNER_REQUIRED. Never edit TASKS.md or ChatGPT audits. Never start M05.

Reuse the M03 camera, AR/motion, quality, storage and diagnostics architecture. Coverage and auto-capture must consume authoritative accepted-capture/pose state and must not create a second sensor or still-capture owner.

## Mandatory implementation

1. Define a detail-pass model for closure, neck and shoulder coverage using elevated viewpoints compatible with non-LiDAR iPhone capture.
2. Keep detail-pass captures part of the same session/quality/pose pipeline and mark them with explicit pass metadata.
3. Require quality and duplicate checks while allowing tighter framing appropriate for closure detail.
4. Expose explicit guidance for missing neck/top sectors.
5. Add tests for pass activation, sector completion, framing policy and unavailable pose.

## Validation

Add deterministic behavior tests for normal, unavailable, failure and exact-boundary conditions. Run relevant regression/project/static checks, `git diff --check`, protected-file checks and privacy/signing review. Do not claim physical iPhone validation unless actually performed.

Create a distinct implementation commit, then a separate log-only commit. User-facing repository links must be full GitHub URLs.

End the log exactly:

`READY_FOR_INDEPENDENT_AUDIT`
