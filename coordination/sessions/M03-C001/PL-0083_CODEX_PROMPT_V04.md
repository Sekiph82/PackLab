# PL-0083 — Codex Remediation Work Order V04

Task: **PL-0083 — Tracking runtime integration-test closure**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CODEX_PROMPT_V03.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0083_CHATGPT_AUDIT_V03.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0083_CODEX_PROMPT_V04.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0083_CHATGPT_AUDIT_CRITERIA_V04.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0083_CODEX_LOG_V04.md

TASKS.md must authorize M03-BATCH-004 / READY / CODEX. Preserve PL-0070 acceptance and PL-0068 OWNER_REQUIRED. Never edit TASKS.md/audits. Never start M04.

Preserve current working Batch-003 implementation and close only the remaining frozen evidence/integration boundary.

## Mandatory remediation
1. Preserve CaptureRuntimeViewModel's live 100 ms tracking refresh and TrackingRecoveryPolicy integration.
2. Add an injected ARTrackingService sequence/fake and tests against CaptureRuntimeViewModel proving limited/normal flapping requires the configured stable-frame hysteresis before pose eligibility/UI warning clears.
3. Prove tracking diagnostics accumulate across those real runtime refreshes and stop changing after runtime stop.
4. Keep production UI driven from the stabilized snapshot.

Where Apple frameworks cannot run on Windows, add injectable production-used seams and conditional XCTest sources; report native execution honestly.

Create one implementation commit and one log-only commit ending:

`READY_FOR_INDEPENDENT_AUDIT`
