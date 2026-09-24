# PL-0101 — Codex Remediation Work Order V02

Repository: https://github.com/Sekiph82/PackLab
Master remediation: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/MASTER_REMEDIATION_CODEX_PROMPT_V01.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0101_CHATGPT_AUDIT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0101_CHATGPT_AUDIT_CRITERIA_V02.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0101_CODEX_LOG_V02.md

TASKS.md must authorize M04-BATCH-002 / READY / CODEX. Preserve accepted M03 and PL-0111. PL-0068 remains OWNER_REQUIRED. Never edit TASKS.md/ChatGPT audits. Never start M05.

Preserve V01 model work and close the production guided-capture integration gap.

## Mandatory remediation
1. Call QualityCandidateLogStore from the real candidate runtime for every analyzed candidate, including rejected candidates and accepted candidates.
2. Bind each log to the active session/capture/sequence and monotonic candidate time without mutating immutable source bytes or accepted session state.
3. Ensure reopen/resume continues a bounded ordered log and rejected-candidate logging cannot corrupt the canonical accepted-capture transaction.
4. Add tests for accepted and rejected entries, ordering, max-record trimming, fresh-store reopen, corrupt-log fail-closed behavior and realistic privacy sanitization.

Run integrated behavior tests plus relevant regression/static/project checks, git diff --check and protected/privacy checks. Create distinct implementation and log-only commits. User-facing links must be full GitHub URLs. End exactly `READY_FOR_INDEPENDENT_AUDIT`.
