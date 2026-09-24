# PL-0118 — Codex Remediation Work Order V02

Repository: https://github.com/Sekiph82/PackLab
Master remediation: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/MASTER_REMEDIATION_CODEX_PROMPT_V01.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0118_CHATGPT_AUDIT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0118_CHATGPT_AUDIT_CRITERIA_V02.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0118_CODEX_LOG_V02.md

TASKS.md must authorize M04-BATCH-002 / READY / CODEX. Preserve M03 and accepted PL-0111. PL-0068 remains OWNER_REQUIRED. Never edit TASKS.md/ChatGPT audits. Never start M05.

Preserve V01 preset/protocol/preflight work and connect it to the shared production M04 runtime.

## Mandatory remediation
1. Replace hard-coded `cameraReady`, `sessionReady` and `storageAvailable` values in NewScanWizard with production readiness supplied from CaptureRuntimeViewModel/session storage/camera binding.
2. Evaluate real health admission, camera readiness, session/storage readiness, selected preset preparation state and PL-0068 calibration availability before scan start.
3. Persist the exact preflight result and acknowledgements in NewScanDraft/M04ScanContext and block Start only for deterministic blocker reasons.
4. Add integrated New Scan tests for actual readiness transitions, hard health stop, unavailable camera/storage/session, ownerRequired calibration warning, all presets and exact start eligibility.

Run integrated behavior/navigation/persistence tests plus relevant regression/static/project checks, git diff --check and protected/privacy checks. Do not claim unavailable physical validation. Create distinct implementation and log-only commits. User-facing links must be full GitHub URLs. End exactly `READY_FOR_INDEPENDENT_AUDIT`.
