# PL-0113 — Codex Remediation Work Order V02

Repository: https://github.com/Sekiph82/PackLab
Master remediation: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/MASTER_REMEDIATION_CODEX_PROMPT_V01.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0113_CHATGPT_AUDIT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0113_CHATGPT_AUDIT_CRITERIA_V02.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0113_CODEX_LOG_V02.md

TASKS.md must authorize M04-BATCH-002 / READY / CODEX. Preserve M03 and accepted PL-0111. PL-0068 remains OWNER_REQUIRED. Never edit TASKS.md/ChatGPT audits. Never start M05.

Preserve V01 preset/protocol/preflight work and connect it to the shared production M04 runtime.

## Mandatory remediation
1. Add a transparent-packaging preparation flow in New Scan/Capture Protocol with an explicit TransparentTreatmentMode selector.
2. Require acknowledgement and record the selected treatment mode truthfully; `.none` must not be silently represented as treated.
3. Persist treatment/acknowledgement in M04ScanContext and use it in ScanSuitabilityPreflight warnings/blockers without claiming physical verification.
4. Add tests for every treatment option, no acknowledgement, acknowledgement, context persistence/reopen and no-false-suitability behavior.

Run integrated behavior/navigation/persistence tests plus relevant regression/static/project checks, git diff --check and protected/privacy checks. Do not claim unavailable physical validation. Create distinct implementation and log-only commits. User-facing links must be full GitHub URLs. End exactly `READY_FOR_INDEPENDENT_AUDIT`.
