# PL-0101 — Codex Work Order V01

Task: **PL-0101 — Per-frame quality metrics logging**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/MASTER_CODEX_PROMPT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0101_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0101_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0101_CODEX_LOG_V01.md

## Authorization

TASKS.md must authorize `M04-BATCH-001` / `READY` / `CODEX`. M03 must remain accepted. PL-0068 must remain unchecked / OWNER_REQUIRED. Never edit TASKS.md or ChatGPT audit artifacts. Never start M05.

Use the existing M03 camera, ARTrackingService, MotionService, accepted-capture, session-storage and diagnostics contracts. Do not create parallel sensor/capture ownership.

## Mandatory implementation

1. Persist quality metrics and decision/reason codes for every candidate frame, including rejected candidates and accepted stills.
2. Bind logs to capture/session identity and monotonic capture timing without modifying immutable source image bytes.
3. Use bounded/structured diagnostics suitable for later Windows tuning and privacy rules; no private path/token leakage.
4. Make logging crash-safe enough that a rejected candidate does not corrupt accepted-session state.
5. Add tests for accepted/rejected candidate logging, ordering, bounded growth, resume/reopen and privacy sanitization.

## Evidence and validation

Add behavior-bearing tests for success, failure, unavailable-data and threshold/boundary cases. Run all relevant deterministic tests/project checks available on the host, `git diff --check`, protected-file checks, and privacy/signing review. Native iPhone/Xcode or physical calibration may be claimed only if actually executed.

Create a distinct implementation commit, then publish the child log in a separate log-only commit. User-facing repository links must be full GitHub URLs, never local filesystem paths.

End the log exactly:

`READY_FOR_INDEPENDENT_AUDIT`
