# PL-0100 — Codex Remediation Work Order V02

Repository: https://github.com/Sekiph82/PackLab
Master remediation: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/MASTER_REMEDIATION_CODEX_PROMPT_V01.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0100_CHATGPT_AUDIT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0100_CHATGPT_AUDIT_CRITERIA_V02.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0100_CODEX_LOG_V02.md

TASKS.md must authorize M04-BATCH-002 / READY / CODEX. Preserve accepted M03 and PL-0111. PL-0068 remains OWNER_REQUIRED. Never edit TASKS.md/ChatGPT audits. Never start M05.

Preserve V01 model work and close the production guided-capture integration gap.

## Mandatory remediation
1. Fix QualityDecisionEngine so `rejectUnavailableClipping == true` actually produces a hard reject for unavailable highlight/shadow metrics.
2. Make QualityDecisionEngine the authoritative decision used by the production M04 candidate runtime after all six metric inputs are computed.
3. Preserve stable reason ordering/deduplication and deterministic unavailable/warning/hard-reject precedence.
4. Add table-driven tests for all hard/warning/unavailable combinations, policy switches and equality at every relevant threshold.

Run integrated behavior tests plus relevant regression/static/project checks, git diff --check and protected/privacy checks. Create distinct implementation and log-only commits. User-facing links must be full GitHub URLs. End exactly `READY_FOR_INDEPENDENT_AUDIT`.
