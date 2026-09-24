# PL-0095 — Codex Remediation Work Order V02

Repository: https://github.com/Sekiph82/PackLab
Master remediation: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/MASTER_REMEDIATION_CODEX_PROMPT_V01.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0095_CHATGPT_AUDIT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0095_CHATGPT_AUDIT_CRITERIA_V02.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0095_CODEX_LOG_V02.md

TASKS.md must authorize M04-BATCH-002 / READY / CODEX. Preserve accepted M03 and PL-0111. PL-0068 remains OWNER_REQUIRED. Never edit TASKS.md/ChatGPT audits. Never start M05.

Preserve the useful V01 algorithm. Close the independent-audit findings through the single production M04 candidate-quality runtime.

## Mandatory remediation
1. Correct the motion status reason interpolation so stale/unavailable reason codes are stable and truthful.
2. Compose MotionBlurAnalyzer into the same production candidate runtime using the existing timestamp-aligned MotionCaptureBinding/MotionService evidence.
3. Publish motion-blur warnings/reasons through the live quality state/UI; unavailable motion alone must not hard reject a sharp frame.
4. Add tests for aligned/stale/missing motion, low/high rotation, sharp/blurred combinations and exact warning/high-risk thresholds at the runtime seam.

Run behavior tests at the production-used seam plus relevant regression/static/project checks, git diff --check, protected-file and privacy/signing checks. Do not claim unavailable physical iPhone calibration.

Create one implementation commit and one separate log-only commit. User-facing links must be full GitHub URLs. End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
