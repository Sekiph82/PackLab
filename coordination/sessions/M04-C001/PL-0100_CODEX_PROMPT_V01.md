# PL-0100 — Codex Work Order V01

Task: **PL-0100 — Deterministic per-frame ACCEPT/REJECT quality decision**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/MASTER_CODEX_PROMPT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0100_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0100_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0100_CODEX_LOG_V01.md

## Authorization

TASKS.md must authorize `M04-BATCH-001` / `READY` / `CODEX`. M03 must remain accepted. PL-0068 must remain unchecked / OWNER_REQUIRED. Never edit TASKS.md or ChatGPT audit artifacts. Never start M05.

Use the existing M03 camera, ARTrackingService, MotionService, accepted-capture, session-storage and diagnostics contracts. Do not create parallel sensor/capture ownership.

## Mandatory implementation

1. Create one authoritative quality decision model that combines sharpness, motion blur, highlight clipping, shadow clipping, framing and background metrics.
2. Decision must be deterministic and explainable with stable reason codes plus raw metric values; no black-box AI score.
3. Define policy for unavailable optional metrics, warning-only conditions, hard reject conditions and exact threshold boundaries.
4. Ensure a candidate cannot be marked ACCEPT when any configured hard-reject condition is present.
5. Add table-driven tests spanning combinations, precedence, unavailable metrics and boundary equality.

## Evidence and validation

Add behavior-bearing tests for success, failure, unavailable-data and threshold/boundary cases. Run all relevant deterministic tests/project checks available on the host, `git diff --check`, protected-file checks, and privacy/signing review. Native iPhone/Xcode or physical calibration may be claimed only if actually executed.

Create a distinct implementation commit, then publish the child log in a separate log-only commit. User-facing repository links must be full GitHub URLs, never local filesystem paths.

End the log exactly:

`READY_FOR_INDEPENDENT_AUDIT`
