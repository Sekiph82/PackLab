# PL-0103 — Codex Remediation Work Order V02

Repository: https://github.com/Sekiph82/PackLab
Master remediation: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/MASTER_REMEDIATION_CODEX_PROMPT_V01.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0103_CHATGPT_AUDIT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0103_CHATGPT_AUDIT_CRITERIA_V02.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0103_CODEX_LOG_V02.md

TASKS.md must authorize M04-BATCH-002 / READY / CODEX. Preserve accepted M03 and PL-0111. PL-0068 remains OWNER_REQUIRED. Never edit TASKS.md/ChatGPT audits. Never start M05.

Preserve V01 model work and close the production guided-capture integration gap.

## Mandatory remediation
1. Present CoverageGridView in the real guided-capture UI and drive it from the authoritative active-session OrbitCoverageModel.
2. Update coverage immediately after accepted captures and expose the currently targeted/missing sector; unavailable evidence must render unavailable rather than synthetic missing/captured state.
3. Keep the view independent from AR ownership and add accessible text fallback.
4. Add runtime/view-model tests for empty, partial, complete, targeted, unavailable and accepted-capture update transitions.

Run integrated behavior tests plus relevant regression/static/project checks, git diff --check and protected/privacy checks. Create distinct implementation and log-only commits. User-facing links must be full GitHub URLs. End exactly `READY_FOR_INDEPENDENT_AUDIT`.
