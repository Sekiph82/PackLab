# PL-0076 — Codex Remediation Work Order V05

Task: **PL-0076 — Encoded photo-schema validation closure**
Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CODEX_PROMPT_V04.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0076_CHATGPT_AUDIT_V04.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0076_CODEX_PROMPT_V05.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0076_CHATGPT_AUDIT_CRITERIA_V05.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0076_CODEX_LOG_V05.md

TASKS.md must authorize M03-BATCH-005 / READY / CODEX. Preserve PL-0068 OWNER_REQUIRED and all accepted M03 children. Never edit TASKS.md/audits. Never start M04.

## Mandatory remediation
1. Add a real schema-validation test path that takes encoded PackScanPhotoMetadataDocument JSON and validates it against schemas/packscan/photo-metadata.schema.json or a mechanically generated validator derived from that schema.
2. Cover available, estimated, unavailable and not_recorded for focal length, exposure, ISO and white balance, including numeric bounds and forbidden value/unit/source combinations.
3. Keep app-only fields out of the strict wire object and preserve current ISO fail-closed mapping.
4. Fail the authoritative contract test on structural/schema drift, not only source-string drift.

Preserve all correct Batch-004 work. Add behavior-bearing tests at the production-used seam. Run focused/relevant regression, static/project, git diff --check and protected/privacy checks truthfully.

Create one implementation commit and one log-only commit. User-facing links must be full GitHub URLs, never local paths. End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
