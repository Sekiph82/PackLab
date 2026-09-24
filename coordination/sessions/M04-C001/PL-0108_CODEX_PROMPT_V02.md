# PL-0108 — Codex Remediation Work Order V02

Repository: https://github.com/Sekiph82/PackLab
Master remediation: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/MASTER_REMEDIATION_CODEX_PROMPT_V01.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0108_CHATGPT_AUDIT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0108_CHATGPT_AUDIT_CRITERIA_V02.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0108_CODEX_LOG_V02.md

TASKS.md must authorize M04-BATCH-002 / READY / CODEX. Preserve M03 and accepted PL-0111. PL-0068 remains OWNER_REQUIRED. Never edit TASKS.md/ChatGPT audits. Never start M05.

Preserve V01 coverage/pass policy work and integrate it into the one production guided-capture session.

## Mandatory remediation
1. Integrate the base pass into the active session with explicit physically-feasible / unavailable / skipped / incomplete / complete state persisted in session diagnostics.
2. Use the same authoritative pose, quality and duplicate rules as other accepted captures when the pass is feasible.
3. Never claim base completion for unavailable/unsafe handling; preserve the explicit reason code.
4. Add tests for feasible complete/incomplete, unavailable/skipped, quality/pose failure and reopen/persistence of pass status.

Run behavior tests at the production session/runtime seam, relevant regression/static/project checks, git diff --check and protected/privacy checks. Create distinct implementation and log-only commits. User-facing links must be full GitHub URLs. End exactly `READY_FOR_INDEPENDENT_AUDIT`.
