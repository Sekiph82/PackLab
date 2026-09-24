# PL-0107 — Codex Remediation Work Order V02

Repository: https://github.com/Sekiph82/PackLab
Master remediation: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/MASTER_REMEDIATION_CODEX_PROMPT_V01.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0107_CHATGPT_AUDIT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0107_CHATGPT_AUDIT_CRITERIA_V02.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0107_CODEX_LOG_V02.md

TASKS.md must authorize M04-BATCH-002 / READY / CODEX. Preserve M03 and accepted PL-0111. PL-0068 remains OWNER_REQUIRED. Never edit TASKS.md/ChatGPT audits. Never start M05.

Preserve V01 coverage/pass policy work and integrate it into the one production guided-capture session.

## Mandatory remediation
1. Integrate top/neck/closure detail passes into the active guided-capture runtime with explicit CapturePassMetadata persisted alongside accepted capture/session evidence.
2. Require authoritative pose coverage, framing quality, overall QualityDecision and NearDuplicateDetector approval for detail-pass acceptance.
3. Use tighter detail framing without changing the selected main-wide camera ownership.
4. Expose missing top/neck/closure guidance live and add tests for activation, quality reject, duplicate reject, unavailable pose, framing boundaries and persisted pass metadata.

Run behavior tests at the production session/runtime seam, relevant regression/static/project checks, git diff --check and protected/privacy checks. Create distinct implementation and log-only commits. User-facing links must be full GitHub URLs. End exactly `READY_FOR_INDEPENDENT_AUDIT`.
