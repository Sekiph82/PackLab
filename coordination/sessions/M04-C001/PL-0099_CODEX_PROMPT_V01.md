# PL-0099 — Codex Work Order V01

Task: **PL-0099 — Background-complexity warning**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/MASTER_CODEX_PROMPT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0099_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0099_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0099_CODEX_LOG_V01.md

## Authorization

TASKS.md must authorize `M04-BATCH-001` / `READY` / `CODEX`. M03 must remain accepted. PL-0068 must remain unchecked / OWNER_REQUIRED. Never edit TASKS.md or ChatGPT audit artifacts. Never start M05.

Use the existing M03 camera, ARTrackingService, MotionService, accepted-capture, session-storage and diagnostics contracts. Do not create parallel sensor/capture ownership.

## Mandatory implementation

1. Implement a deterministic background-complexity metric that warns about busy/feature-confusing setups without treating the product itself as background.
2. Use a bounded image-analysis strategy appropriate for live mobile evaluation and avoid heavy reconstruction/segmentation dependencies.
3. Return explainable metrics and warning reason(s); background complexity alone should follow the frozen policy for warning versus reject rather than hidden heuristics.
4. Keep matte/simple background guidance compatible with packaging presets.
5. Add tests for clean matte background, moderate texture, highly cluttered background and unavailable/object-mask cases.

## Evidence and validation

Add behavior-bearing tests for success, failure, unavailable-data and threshold/boundary cases. Run all relevant deterministic tests/project checks available on the host, `git diff --check`, protected-file checks, and privacy/signing review. Native iPhone/Xcode or physical calibration may be claimed only if actually executed.

Create a distinct implementation commit, then publish the child log in a separate log-only commit. User-facing repository links must be full GitHub URLs, never local filesystem paths.

End the log exactly:

`READY_FOR_INDEPENDENT_AUDIT`
