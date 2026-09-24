# PL-0116 — Codex Work Order V01

Task: **PL-0116 — Turntable mode**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/MASTER_CODEX_PROMPT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0116_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0116_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0116_CODEX_LOG_V01.md

## Authorization

TASKS.md must authorize `M04-BATCH-001` / `READY` / `CODEX`. M03 remains accepted. PL-0068 remains unchecked / OWNER_REQUIRED. Never edit TASKS.md or ChatGPT audits. Never start M05.

Reuse the shared M04 quality/coverage engine and the accepted M03 capture/session architecture. Presets and modes configure authoritative shared policies; they must not fork new capture/sensor pipelines.

## Mandatory implementation

1. Implement a deterministic turntable capture mode with angle-indexed sectors and explicit assumptions about static camera/background versus rotating object.
2. Keep turntable pose/angle evidence distinct from freehand AR world-pose evidence and record the evidence source truthfully.
3. Define duplicate/coverage/completion rules for expected turntable angles, including missed and repeated angles.
4. Keep object/background masking assumptions as metadata/guidance only; do not start M08 segmentation implementation.
5. Add tests for angle indexing, wrap-around, missing/repeated angles, completion and evidence-source labeling.

## Validation

Add behavior-bearing tests for preset/mode policy, persistence, warnings/blockers and exact boundaries. Run all relevant regression/project/static checks, `git diff --check`, protected-file and privacy/signing checks. Do not claim physical packaging/iPhone validation unless actually executed.

Create a distinct implementation commit and separate log-only commit. User-facing repository links must be full GitHub URLs.

End the log exactly:

`READY_FOR_INDEPENDENT_AUDIT`
