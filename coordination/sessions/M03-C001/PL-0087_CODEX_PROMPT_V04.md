# PL-0087 — Codex Remediation Work Order V04

Task: **PL-0087 — New Scan exact-callback test closure**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CODEX_PROMPT_V03.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0087_CHATGPT_AUDIT_V03.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0087_CODEX_PROMPT_V04.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0087_CHATGPT_AUDIT_CRITERIA_V04.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0087_CODEX_LOG_V04.md

TASKS.md must authorize M03-BATCH-004 / READY / CODEX. Preserve PL-0070 acceptance and PL-0068 OWNER_REQUIRED. Never edit TASKS.md/audits. Never start M04.

Preserve current working Batch-003 implementation and close only the remaining frozen evidence/integration boundary.

## Mandatory remediation
1. Preserve NewScanWizard's use of NewScanWorkflowModel and ContentView's real ScanSessionStore/ActiveScanSession handoff.
2. Extract the Start/Cancel action into a small testable coordinator used by the view, or otherwise make the actual callback seam directly testable.
3. Prove one valid Start calls onStart exactly once with normalized values, invalid Start calls it zero times and keeps visible validation state, and Cancel calls Start zero times.
4. Preserve all M02 capture-mode IDs and real session creation on successful Start.

Where Apple frameworks cannot run on Windows, add injectable production-used seams and conditional XCTest sources; report native execution honestly.

Create one implementation commit and one log-only commit ending:

`READY_FOR_INDEPENDENT_AUDIT`
