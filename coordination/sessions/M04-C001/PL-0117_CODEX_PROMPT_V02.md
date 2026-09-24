# PL-0117 — Codex Remediation Work Order V02

Repository: https://github.com/Sekiph82/PackLab
Master remediation: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/MASTER_REMEDIATION_CODEX_PROMPT_V01.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0117_CHATGPT_AUDIT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0117_CHATGPT_AUDIT_CRITERIA_V02.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0117_CODEX_LOG_V02.md

TASKS.md must authorize M04-BATCH-002 / READY / CODEX. Preserve M03 and accepted PL-0111. PL-0068 remains OWNER_REQUIRED. Never edit TASKS.md/ChatGPT audits. Never start M05.

Preserve V01 preset/protocol/preflight work and connect it to the shared production M04 runtime.

## Mandatory remediation
1. Insert CaptureProtocolView into the real New Scan flow after preset selection and before preflight/start; remove the generic toggle as a substitute for preset-specific protocol presentation.
2. Drive protocol content from versioned preset data and retain acknowledgement state only where required.
3. Make protocol guidance accessible from the active scan without corrupting session state.
4. Add navigation/view-model tests for all presets, transparent acknowledgement requirement, continue/cancel behavior and persisted acknowledgement.

Run integrated behavior/navigation/persistence tests plus relevant regression/static/project checks, git diff --check and protected/privacy checks. Do not claim unavailable physical validation. Create distinct implementation and log-only commits. User-facing links must be full GitHub URLs. End exactly `READY_FOR_INDEPENDENT_AUDIT`.
