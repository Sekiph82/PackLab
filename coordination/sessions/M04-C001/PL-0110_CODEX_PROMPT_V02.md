# PL-0110 — Codex Remediation Work Order V02

Repository: https://github.com/Sekiph82/PackLab
Master remediation: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/MASTER_REMEDIATION_CODEX_PROMPT_V01.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0110_CHATGPT_AUDIT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0110_CHATGPT_AUDIT_CRITERIA_V02.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0110_CODEX_LOG_V02.md

TASKS.md must authorize M04-BATCH-002 / READY / CODEX. Preserve M03 and accepted PL-0111. PL-0068 remains OWNER_REQUIRED. Never edit TASKS.md/ChatGPT audits. Never start M05.

Preserve V01 coverage/pass policy work and integrate it into the one production guided-capture session.

## Mandatory remediation
1. Add a real manual capture action in the guided-capture UI/runtime that evaluates ManualCaptureCoordinator and, when allowed, invokes the same health-gated still-capture/session transaction used by auto capture.
2. Manual override may bypass auto-quality/coverage gating only as frozen; it must never bypass health hard stop, camera/session readiness, source integrity or required metadata/evidence constraints.
3. Persist manual-override warnings/reasons with the candidate/accepted quality log and accepted capture context.
4. Synchronize auto-capture cooldown/in-flight state after manual capture and add tests for warning override, hard blockers, persistence, rejected/manual success and auto/manual interaction.

Run behavior tests at the production session/runtime seam, relevant regression/static/project checks, git diff --check and protected/privacy checks. Create distinct implementation and log-only commits. User-facing links must be full GitHub URLs. End exactly `READY_FOR_INDEPENDENT_AUDIT`.
