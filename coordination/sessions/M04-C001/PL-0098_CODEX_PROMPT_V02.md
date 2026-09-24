# PL-0098 — Codex Remediation Work Order V02

Repository: https://github.com/Sekiph82/PackLab
Master remediation: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/MASTER_REMEDIATION_CODEX_PROMPT_V01.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0098_CHATGPT_AUDIT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0098_CHATGPT_AUDIT_CRITERIA_V02.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0098_CODEX_LOG_V02.md

TASKS.md must authorize M04-BATCH-002 / READY / CODEX. Preserve accepted M03 and PL-0111. PL-0068 remains OWNER_REQUIRED. Never edit TASKS.md/ChatGPT audits. Never start M05.

Preserve the useful V01 algorithm. Close the independent-audit findings through the single production M04 candidate-quality runtime.

## Mandatory remediation
1. Wire FramingAnalyzer into the production candidate runtime and publish too-small/acceptable/cropped state plus metrics/reasons to the live capture UI.
2. Feed the same framing metric into CandidateQualityMetrics and the candidate log store.
3. Keep object-mask input as the accepted bounded contract without starting M08 segmentation.
4. Add tests for too-small, centered-good, edge-touching, oversized-by-area, unavailable mask and exact size/margin boundaries at the runtime seam.

Run behavior tests at the production-used seam plus relevant regression/static/project checks, git diff --check, protected-file and privacy/signing checks. Do not claim unavailable physical iPhone calibration.

Create one implementation commit and one separate log-only commit. User-facing links must be full GitHub URLs. End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
