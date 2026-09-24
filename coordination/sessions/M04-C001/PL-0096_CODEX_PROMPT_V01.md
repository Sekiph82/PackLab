# PL-0096 — Codex Work Order V01

Task: **PL-0096 — Exposure and highlight clipping analysis for glossy plastic**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/MASTER_CODEX_PROMPT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0096_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0096_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0096_CODEX_LOG_V01.md

## Authorization

TASKS.md must authorize `M04-BATCH-001` / `READY` / `CODEX`. M03 must remain accepted. PL-0068 must remain unchecked / OWNER_REQUIRED. Never edit TASKS.md or ChatGPT audit artifacts. Never start M05.

Use the existing M03 camera, ARTrackingService, MotionService, accepted-capture, session-storage and diagnostics contracts. Do not create parallel sensor/capture ownership.

## Mandatory implementation

1. Implement deterministic luminance/highlight clipping analysis on candidate frames with explicit clipping percentage/statistics.
2. Support glossy packaging where small specular highlights may be tolerated but broad clipping must warn/reject according to configurable thresholds.
3. Keep analysis independent from camera exposure-lock control while consuming existing capture metadata when useful for diagnostics.
4. Expose explainable reasons and raw metrics for later tuning.
5. Add tests for no clipping, localized highlights, broad clipping and exact threshold boundaries.

## Evidence and validation

Add behavior-bearing tests for success, failure, unavailable-data and threshold/boundary cases. Run all relevant deterministic tests/project checks available on the host, `git diff --check`, protected-file checks, and privacy/signing review. Native iPhone/Xcode or physical calibration may be claimed only if actually executed.

Create a distinct implementation commit, then publish the child log in a separate log-only commit. User-facing repository links must be full GitHub URLs, never local filesystem paths.

End the log exactly:

`READY_FOR_INDEPENDENT_AUDIT`
