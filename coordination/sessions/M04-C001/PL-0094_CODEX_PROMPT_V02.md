# PL-0094 — Codex Remediation Work Order V02

Repository: https://github.com/Sekiph82/PackLab
Master remediation: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/MASTER_REMEDIATION_CODEX_PROMPT_V01.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0094_CHATGPT_AUDIT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0094_CHATGPT_AUDIT_CRITERIA_V02.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0094_CODEX_LOG_V02.md

TASKS.md must authorize M04-BATCH-002 / READY / CODEX. Preserve accepted M03 and PL-0111. PL-0068 remains OWNER_REQUIRED. Never edit TASKS.md/ChatGPT audits. Never start M05.

Preserve the useful V01 algorithm. Close the independent-audit findings through the single production M04 candidate-quality runtime.

## Mandatory remediation
1. Correct the sharpness reason-code interpolation so produced codes are stable `sharpness_accept`, `sharpness_warn`, `sharpness_reject` rather than the current literal placeholder.
2. Wire SharpnessAnalyzer into the production M04 candidate-frame runtime fed by the existing camera preview/candidate analysis seam; do not create a second camera owner.
3. Keep thresholds configurable/provisional and preserve SharpnessCalibrationHarness truthfulness.
4. Add deterministic tests for sharp, mildly blurred, strongly blurred, unavailable and exact accept/warn boundaries, plus runtime propagation into CandidateQualityMetrics.

Run behavior tests at the production-used seam plus relevant regression/static/project checks, git diff --check, protected-file and privacy/signing checks. Do not claim unavailable physical iPhone calibration.

Create one implementation commit and one separate log-only commit. User-facing links must be full GitHub URLs. End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
