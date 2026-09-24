# PL-0106 — Codex Remediation Work Order V02

Repository: https://github.com/Sekiph82/PackLab
Master remediation: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/MASTER_REMEDIATION_CODEX_PROMPT_V01.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0106_CHATGPT_AUDIT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0106_CHATGPT_AUDIT_CRITERIA_V02.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0106_CODEX_LOG_V02.md

TASKS.md must authorize M04-BATCH-002 / READY / CODEX. Preserve M03 and accepted PL-0111. PL-0068 remains OWNER_REQUIRED. Never edit TASKS.md/ChatGPT audits. Never start M05.

Preserve V01 coverage/pass policy work and integrate it into the one production guided-capture session.

## Mandatory remediation
1. Drive StandardBottleCoveragePolicy from the active preset/session configuration and accepted OrbitCoverageModel rather than a standalone evaluation call.
2. Publish lower/middle/upper ring status and missing-ring guidance to the live guided-capture UI and structured session diagnostics.
3. Completion must require every mandatory ring regardless of total accepted frame count.
4. Add tests for uneven coverage, each missing ring, all-complete state, exact elevation/sector boundaries and live guidance updates.

Run behavior tests at the production session/runtime seam, relevant regression/static/project checks, git diff --check and protected/privacy checks. Create distinct implementation and log-only commits. User-facing links must be full GitHub URLs. End exactly `READY_FOR_INDEPENDENT_AUDIT`.
