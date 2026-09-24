# PL-0104 — Codex Remediation Work Order V02

Repository: https://github.com/Sekiph82/PackLab
Master remediation: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/MASTER_REMEDIATION_CODEX_PROMPT_V01.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0104_CHATGPT_AUDIT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0104_CHATGPT_AUDIT_CRITERIA_V02.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0104_CODEX_LOG_V02.md

TASKS.md must authorize M04-BATCH-002 / READY / CODEX. Preserve accepted M03 and PL-0111. PL-0068 remains OWNER_REQUIRED. Never edit TASKS.md/ChatGPT audits. Never start M05.

Preserve V01 model work and close the production guided-capture integration gap.

## Mandatory remediation
1. Compose GuidedAutoCaptureService into the production M04 runtime with live pose eligibility, target coverage sector, QualityDecision, duplicate/overlap permission and the existing health-gated still capture service.
2. Ensure auto capture cannot issue duplicate/in-flight requests and define deterministic cooldown/rearm after accepted and rejected attempts.
3. On accepted still, route through the existing immutable source/session transaction and authoritative coverage/quality logging updates.
4. Add integrated tests for every gate reason, quality reject, missing target, pose ineligible, overlap blocked, health hard stop, in-flight, cooldown boundary, rejected rearm and accepted capture.

Run integrated behavior tests plus relevant regression/static/project checks, git diff --check and protected/privacy checks. Create distinct implementation and log-only commits. User-facing links must be full GitHub URLs. End exactly `READY_FOR_INDEPENDENT_AUDIT`.
