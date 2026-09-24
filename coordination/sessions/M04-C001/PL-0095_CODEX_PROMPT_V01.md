# PL-0095 — Codex Work Order V01

Task: **PL-0095 — Motion-blur warning using frame analysis plus CoreMotion**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/MASTER_CODEX_PROMPT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0095_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0095_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0095_CODEX_LOG_V01.md

## Authorization

TASKS.md must authorize `M04-BATCH-001` / `READY` / `CODEX`. M03 must remain accepted. PL-0068 must remain unchecked / OWNER_REQUIRED. Never edit TASKS.md or ChatGPT audit artifacts. Never start M05.

Use the existing M03 camera, ARTrackingService, MotionService, accepted-capture, session-storage and diagnostics contracts. Do not create parallel sensor/capture ownership.

## Mandatory implementation

1. Combine image-domain blur evidence with existing timestamp-aligned MotionService rotation-rate evidence.
2. Define a deterministic warning decision that distinguishes image blur with low motion, high motion with acceptable sharpness, stale/unavailable motion data and combined high-risk blur.
3. Use accepted M03 timestamp semantics and never align wall-clock values directly to CoreMotion monotonic timestamps.
4. Expose warning reason(s) to capture runtime/UI without silently rejecting on unavailable motion alone.
5. Add tests for aligned/stale/missing motion, high rotation, low/high blur and threshold boundaries.

## Evidence and validation

Add behavior-bearing tests for success, failure, unavailable-data and threshold/boundary cases. Run all relevant deterministic tests/project checks available on the host, `git diff --check`, protected-file checks, and privacy/signing review. Native iPhone/Xcode or physical calibration may be claimed only if actually executed.

Create a distinct implementation commit, then publish the child log in a separate log-only commit. User-facing repository links must be full GitHub URLs, never local filesystem paths.

End the log exactly:

`READY_FOR_INDEPENDENT_AUDIT`
