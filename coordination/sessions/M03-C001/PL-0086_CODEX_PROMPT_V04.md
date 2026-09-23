# PL-0086 — Codex Remediation Work Order V04

Task: **PL-0086 — Diagnostics privacy/limit evidence closure**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CODEX_PROMPT_V03.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0086_CHATGPT_AUDIT_V03.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0086_CODEX_PROMPT_V04.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0086_CHATGPT_AUDIT_CRITERIA_V04.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0086_CODEX_LOG_V04.md

TASKS.md must authorize M03-BATCH-004 / READY / CODEX. Preserve PL-0070 acceptance and PL-0068 OWNER_REQUIRED. Never edit TASKS.md/audits. Never start M04.

Preserve current working Batch-003 implementation and close only the remaining frozen evidence/integration boundary.

## Mandatory remediation
1. Preserve explicit units, basis_conversion and malformed-data rejection.
2. Add golden tests using realistic Windows/macOS user paths, bearer/API-token-like strings and user-identifying path fragments through the same DiagnosticsSanitizer boundary used by PoseDiagnosticsExporter.
3. Add exact maximumRecords and maximumRecords+1 tests proving bounded export behavior.
4. Verify sanitized output contains no original private path/user/token fragments while valid capture IDs and deterministic ordering remain stable.

Where Apple frameworks cannot run on Windows, add injectable production-used seams and conditional XCTest sources; report native execution honestly.

Create one implementation commit and one log-only commit ending:

`READY_FOR_INDEPENDENT_AUDIT`
