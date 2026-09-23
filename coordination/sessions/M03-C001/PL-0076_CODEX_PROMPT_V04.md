# PL-0076 — Codex Remediation Work Order V04

Task: **PL-0076 — Authoritative photo-schema invariant closure**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CODEX_PROMPT_V03.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0076_CHATGPT_AUDIT_V03.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0076_CODEX_PROMPT_V04.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0076_CHATGPT_AUDIT_CRITERIA_V04.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0076_CODEX_LOG_V04.md

TASKS.md must authorize M03-BATCH-004 / READY / CODEX. PL-0070 remains accepted; PL-0068 remains OWNER_REQUIRED. Never edit TASKS.md or ChatGPT audits. Never start M04.

Preserve Batch-003 progress and close only the remaining audit boundary.

## Mandatory remediation
1. Add a test utility/fixture that validates the encoded Swift PackScan photo metadata document against the authoritative schemas/packscan/photo-metadata.schema.json contract or a mechanically generated equivalent fixture, so schema drift cannot pass local Swift-only checks.
2. Fix ISO mapping so numeric value/source/unit are permitted only for schema-allowed available/estimated states; unavailable/not_recorded must reject all forbidden evidence.
3. Exercise available, estimated, unavailable and not_recorded for focal length, exposure, ISO and white balance, including all minimum/maximum numeric boundaries.
4. Keep app-only lens/timestamp fields outside the strict photo wire object.

Use injected drivers/fakes where needed so Apple-framework behavior is testable in source even if Windows cannot execute Xcode. Run all available regression/static/project checks truthfully.

Create one implementation commit and one log-only commit ending:

`READY_FOR_INDEPENDENT_AUDIT`
