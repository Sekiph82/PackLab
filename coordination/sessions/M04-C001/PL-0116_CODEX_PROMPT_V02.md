# PL-0116 — Codex Remediation Work Order V02

Repository: https://github.com/Sekiph82/PackLab
Master remediation: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/MASTER_REMEDIATION_CODEX_PROMPT_V01.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0116_CHATGPT_AUDIT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0116_CHATGPT_AUDIT_CRITERIA_V02.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0116_CODEX_LOG_V02.md

TASKS.md must authorize M04-BATCH-002 / READY / CODEX. Preserve M03 and accepted PL-0111. PL-0068 remains OWNER_REQUIRED. Never edit TASKS.md/ChatGPT audits. Never start M05.

Preserve V01 preset/protocol/preflight work and connect it to the shared production M04 runtime.

## Mandatory remediation
1. Wire TurntableCoverageModel into the real turntable capture workflow with an explicit deterministic angle input/evidence source for each accepted candidate.
2. Persist turntable angle/sector/evidence-source metadata with accepted captures/session context and keep it distinct from AR freehand pose.
3. Use turntable coverage, duplicate angle and completion rules in live guidance/auto-manual capture decisions.
4. Add tests for angle entry/indexing/wrap, missing/repeated angles, accepted capture persistence/reopen, evidence-source labeling and completion.

Run integrated behavior/navigation/persistence tests plus relevant regression/static/project checks, git diff --check and protected/privacy checks. Do not claim unavailable physical validation. Create distinct implementation and log-only commits. User-facing links must be full GitHub URLs. End exactly `READY_FOR_INDEPENDENT_AUDIT`.
